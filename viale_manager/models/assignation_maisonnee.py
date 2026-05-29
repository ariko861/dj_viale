from django.db import models


class AssignationsMaisonnees(models.Model):
    id = models.BigAutoField(primary_key=True)
    sejour_id = models.BigIntegerField()
    house_id = models.BigIntegerField()
    planning_id = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'assignations_maisonnees'