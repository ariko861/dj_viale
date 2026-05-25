from django.db import models


class Membre(models.Model):

    prenom = models.CharField(max_length=255)
    nom = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=30, blank=True, null=True)

    adresse = models.OneToOneField(
        'Adresse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.prenom} {self.nom}"
