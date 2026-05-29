from django.db import models


class Houses(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    community = models.BooleanField()
    displayhousenamewithroom = models.BooleanField(db_column='displayHouseNameWithRoom')
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'houses'
