from django.db import models, transaction
from django.db.models import F, Max
from django.db.models.functions import Lower, Trim


class Visitors(models.Model):

    id = models.BigAutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    date_de_naissance = models.DateField(blank=True, null=True)
    confirmed = models.BooleanField()
    email = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    remarques = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{str(self.nom).upper()} {self.prenom}"

    @classmethod
    def find_homonym(cls, nom, prenom, date_de_naissance):
        """Visiteur existant de même nom, prénom et date de naissance.

        Comparaison insensible à la casse et aux espaces autour. En cas de
        doublons déjà présents, renvoie celui du séjour le plus récent.

        :return: le visiteur trouvé, ou ``None``.
        """
        if not (nom and prenom and date_de_naissance):
            return None
        return (
            cls.objects
            .annotate(nom_norm=Lower(Trim('nom')), prenom_norm=Lower(Trim('prenom')))
            .filter(
                nom_norm=nom.strip().lower(), prenom_norm=prenom.strip().lower(),
                date_de_naissance=date_de_naissance,
            )
            .annotate(dernier_sejour=Max('sejours__arrival_date'))
            .order_by(F('dernier_sejour').desc(nulls_last=True), '-id')
            .first()
        )

    def _connues(self, field):
        """Valeurs (en minuscules) déjà connues pour ``email`` ou ``phone``."""
        valeurs = {c.value.lower() for c in self.contacts.filter(type=field)}
        if getattr(self, field):
            valeurs.add(getattr(self, field).strip().lower())
        return valeurs

    def add_contact(self, field, value):
        """Ajoute une coordonnée secondaire si elle n'est pas déjà connue.

        :param field: ``'email'`` ou ``'phone'``.
        :param value: valeur à ajouter ; vide = rien ne change.
        """
        from .visitor_contact import VisitorContacts

        value = (value or '').strip()
        if value and value.lower() not in self._connues(field):
            VisitorContacts.objects.create(visitor=self, type=field, value=value)

    def set_coordonnee(self, field, value, replace=True):
        """Met à jour ``email`` ou ``phone`` sans perdre d'information.

        Un champ principal vide est toujours complété. Sinon, avec ``replace``,
        la nouvelle valeur devient principale et l'ancienne passe en coordonnée
        secondaire ; sans ``replace``, la nouvelle valeur est ajoutée en
        secondaire. Les coordonnées secondaires sont enregistrées tout de suite,
        le visiteur lui-même n'est pas sauvegardé.

        :param field: ``'email'`` ou ``'phone'``.
        :param value: nouvelle valeur ; vide = rien ne change.
        :param replace: ``False`` quand l'identité du visiteur n'est pas vérifiée.
        """
        value = (value or '').strip()
        old = (getattr(self, field) or '').strip()
        if not value or value.lower() == old.lower():
            return
        if not old:
            setattr(self, field, value)
        elif replace:
            self.contacts.filter(type=field, value__iexact=value).delete()
            setattr(self, field, value)
            self.add_contact(field, old)
        else:
            self.add_contact(field, value)

    @transaction.atomic
    def absorb(self, others):
        """Fusionne ``others`` dans ce visiteur, puis les supprime.

        Les séjours sont rattachés à ce visiteur. Ses champs vides sont
        complétés par ceux des doublons (le plus récent d'abord) ; leurs
        autres emails et téléphones deviennent des coordonnées secondaires, et
        leurs remarques s'ajoutent aux siennes.

        :param others: visiteurs à absorber (ce visiteur est ignoré s'il y figure).
        :return: le nombre de visiteurs supprimés.
        """
        from .sejour import Sejours

        others = [o for o in others if o.pk != self.pk]
        if not others:
            return 0
        others.sort(key=lambda o: o.pk, reverse=True)

        for field in ('email', 'phone', 'date_de_naissance'):
            if not getattr(self, field):
                setattr(self, field, next((getattr(o, field) for o in others if getattr(o, field)), None))
        self.confirmed = self.confirmed or any(o.confirmed for o in others)
        notes = [self.remarques] + [o.remarques for o in others]
        self.remarques = '\n'.join(n for n in notes if n) or None
        self.save()

        for o in others:
            for field in ('email', 'phone'):
                self.add_contact(field, getattr(o, field))
            for c in o.contacts.all():
                self.add_contact(c.type, c.value)

        Sejours.objects.filter(visitor__in=others).update(visitor=self)
        Visitors.objects.filter(pk__in=[o.pk for o in others]).delete()
        return len(others)

    class Meta:
        db_table = '"viale_manager"."visitors"'
        verbose_name = 'Visiteur'
        ordering = ['nom', 'prenom']
