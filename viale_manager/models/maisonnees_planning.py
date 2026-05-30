from django.db import models


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

    class Meta:
        db_table = '"viale_manager"."maisonnees_planning"'
