from django.db import models


class HousesInMaisonneesPlanning(models.Model):
    house_id = models.BigIntegerField()
    planning_id = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'houses_in_maisonnees_planning'
