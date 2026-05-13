from django.db import models


class TagDocument(models.Model):

    nom = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom