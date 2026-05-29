from django.db import models


class HousesInMaisonneesPlanning(models.Model):


    id = models.BigAutoField(primary_key=True)

    house = models.ForeignKey(
        'Houses',
        on_delete=models.CASCADE,
    )
    planning = models.ForeignKey(
        'MaisonneesPlanning',
        on_delete=models.CASCADE,
    )


    class Meta:
        db_table = '"viale_manager"."houses_in_maisonnees_planning"'
