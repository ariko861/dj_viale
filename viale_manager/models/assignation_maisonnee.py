from django.db import models


class AssignationsMaisonnees(models.Model):

    id = models.BigAutoField(primary_key=True)

    sejour = models.ForeignKey(
        'Sejours',
        on_delete=models.CASCADE,
    )

    house = models.ForeignKey(
        'Houses',
        on_delete=models.CASCADE,
    )

    planning = models.ForeignKey(
        'MaisonneesPlanning',
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = '"viale_manager"."assignations_maisonnees"'