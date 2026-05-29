from django.db import models


class MaisonneesPlanning(models.Model):
    id = models.BigAutoField(primary_key=True)
    begin = models.DateField()
    end = models.DateField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'maisonnees_planning'
