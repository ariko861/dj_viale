from datetime import date, timedelta

from django.db import models, transaction
from django.db.models import Q
from django.utils.formats import date_format


class MaisonneesPlanning(models.Model):
    id = models.BigAutoField(primary_key=True)
    begin = models.DateField()
    end = models.DateField()
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    houses = models.ManyToManyField(
        'Houses',
        through='HousesInMaisonneesPlanning',
    )

    def __str__(self):
        return f"du {date_format(self.begin, 'D j F')} au {date_format(self.end, 'D j F Y')}"

    @classmethod
    def next_period(cls):
        """Dates proposées pour un nouveau planning.

        La semaine qui suit le dernier planning ; à défaut, la semaine en cours.

        :return: ``(debut, fin)``.
        """
        last = cls.objects.filter(end__gte=date.today()).order_by('-end').first()
        if last:
            begin = last.end + timedelta(days=1)
        else:
            today = date.today()
            begin = today - timedelta(days=today.weekday())
        return begin, begin + timedelta(days=6)

    @transaction.atomic
    def prepare(self):
        """Synchronise les assignations avec les séjours présents sur la période.

        Chaque séjour présent au moins un jour sur la période reçoit une
        assignation « à placer » ; celles des séjours qui n'y sont plus (dates
        modifiées depuis) sont retirées.
        """
        from .assignation_maisonnee import AssignationsMaisonnees
        from .sejour import Sejours

        presents = Sejours.objects.filter(arrival_date__lte=self.end).filter(
            Q(departure_date__gte=self.begin) | Q(departure_date__isnull=True)
        )
        self.assignationsmaisonnees_set.exclude(sejour__in=presents).delete()
        deja = self.assignationsmaisonnees_set.values('sejour_id')
        AssignationsMaisonnees.objects.bulk_create([
            AssignationsMaisonnees(planning=self, sejour=s, house=None)
            for s in presents.exclude(id__in=deja)
        ])

    def reset(self):
        """Remet tout le monde « à placer »."""
        self.assignationsmaisonnees_set.update(house=None)
        self.prepare()

    @transaction.atomic
    def set_houses(self, houses):
        """Change les maisons du planning ; les personnes d'une maison retirée repassent « à placer »."""
        self.houses.set(houses)
        self.assignationsmaisonnees_set.exclude(house__in=self.houses.all()).update(house=None)

    class Meta:
        db_table = '"viale_manager"."maisonnees_planning"'
        verbose_name = 'planning des maisonnées'
        verbose_name_plural = 'plannings des maisonnées'
