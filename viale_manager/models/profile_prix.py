from django.db import models


class Profiles(models.Model):

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.FloatField(default=0)
    is_default = models.BooleanField(verbose_name='par défaut')
    remarques = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = '"viale_manager"."profiles"'
