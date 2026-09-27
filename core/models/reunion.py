from django.db import models


class Reunion(models.Model):

    debut = models.DateTimeField()
    fin = models.DateTimeField(null=True, blank=True)

    organe = models.ForeignKey(
        'Organe',
        on_delete=models.CASCADE,
    )

    adresse = models.ForeignKey(
        'Adresse',
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'est_lieu_reunion': True},
    )

    annee = models.PositiveSmallIntegerField(
        'année',
        blank=True,
        db_index=True,
        help_text="Laisser vide pour utiliser l'année de début de la réunion.",
    )

    ordre_du_jour = models.TextField(null=True, blank=True)

    membres = models.ManyToManyField(
        'Membre',
        through='MembreReunion',
    )

    def save(self, *args, **kwargs):
        if self.annee is None:
            self.annee = self.debut.year
        super().save(*args, **kwargs)
        self.documents.exclude(annee=self.annee).update(annee=self.annee)

    @property
    def date_debut(self):
        return self.debut.date()


    def __str__(self):
        return f'{self.organe} - {self.date_debut}'