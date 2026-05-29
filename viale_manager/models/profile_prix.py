from django.db import models


class Profiles(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.FloatField()
    is_default = models.BooleanField()
    remarques = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'profiles'
