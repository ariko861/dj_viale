from django.db import models

class Adresse(models.Model):

    adresse = models.CharField(max_length=255)
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=100)

    est_lieu_reunion = models.BooleanField(default=False)

    nom = models.CharField(max_length=100, null=True, blank=True)


    def __str__(self):
        return f'{self.adresse} - {self.ville} - {self.code_postal}'
