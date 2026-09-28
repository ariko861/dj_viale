from datetime import date

from django.core.exceptions import ValidationError
from django.db import models


class SejoursQuerySet(models.QuerySet):

    def actifs(self):
        """Séjours non terminés : departure_date >= aujourd'hui ou indéterminée."""
        today = date.today()
        return self.filter(
            models.Q(departure_date__gte=today) | models.Q(departure_date__isnull=True)
        )

    def presents(self):
        """Séjours en cours aujourd'hui."""
        today = date.today()
        return self.filter(arrival_date__lte=today).actifs()

    def arrivent_aujourd_hui(self):
        return self.filter(arrival_date=date.today())

    def partent_aujourd_hui(self):
        return self.filter(departure_date=date.today())

    def futurs(self):
        return self.filter(arrival_date__gt=date.today())

    def termines(self):
        return self.filter(departure_date__lt=date.today())

    def pour_periode(self, start_str, end_str):
        """Séjours qui chevauchent la période [start_str, end_str] (format YYYY-MM-DD)."""
        return self.filter(
            arrival_date__lt=end_str,
        ).filter(
            models.Q(departure_date__gte=start_str) | models.Q(departure_date__isnull=True)
        )


class Sejours(models.Model):

    objects = SejoursQuerySet.as_manager()

    id = models.BigAutoField(primary_key=True)

    reservation = models.ForeignKey(
        'Reservations',
        models.DO_NOTHING,
        verbose_name='reservation',
    )

    visitor = models.ForeignKey(
        'Visitors',
        models.PROTECT,
        verbose_name='Visiteur'
    )

    confirmed = models.BooleanField(verbose_name="confirmé", default=False)
    remove_from_stats = models.BooleanField(verbose_name="retirer des statistiques", default=False)
    arrival_date = models.DateField(verbose_name="date d'arrivée")
    departure_date = models.DateField(blank=True, null=True, verbose_name="date de départ")
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    room = models.ForeignKey('Rooms', models.SET_NULL, blank=True, null=True)

    price = models.FloatField(blank=True, null=True, verbose_name="prix")


    @property
    def nuitees(self) -> int | None:
        if self.departure_date is None:
            return None
        return (self.departure_date - self.arrival_date).days


    @property
    def total(self) -> float | None:
        if self.nuitees is None or self.price is None:
            return None
        return self.nuitees * self.price


    def create_break(self, begin, end):
        """Coupe le séjour par une absence du ``begin`` au ``end``.

        Le séjour se termine à ``begin`` ; une copie reprend de ``end`` jusqu'à
        l'ancien départ.

        :param begin: premier jour d'absence (nouvelle date de départ).
        :param end: jour du retour (date d'arrivée de la copie).
        :return: le séjour créé pour la reprise.
        """
        reprise = Sejours.objects.get(pk=self.pk)
        reprise.pk = None
        reprise.arrival_date = end
        reprise.save()
        self.departure_date = begin
        self.save(update_fields=['departure_date', 'updated_at'])
        return reprise

    def clean(self):
        if self.departure_date and self.departure_date <= self.arrival_date:
            raise ValidationError(
                {'departure_date': "La date de départ doit être après la date d'arrivée."}
            )

    def __str__(self):
        return f"{self.visitor} — {self.arrival_date}"

    class Meta:
        db_table = '"viale_manager"."sejours"'

        verbose_name = "séjour"
        permissions = [
            ('view_statistiques', 'Peut voir les statistiques (nuitées et revenus)'),
            ('change_remove_from_stats', 'Peut exclure un séjour des statistiques'),
        ]
