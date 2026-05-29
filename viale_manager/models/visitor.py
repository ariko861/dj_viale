from django.db import models


class Visitors(models.Model):
    id = models.BigAutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    date_de_naissance = models.DateField(blank=True, null=True)
    confirmed = models.BooleanField()
    email = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    remarques = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'visitors'
