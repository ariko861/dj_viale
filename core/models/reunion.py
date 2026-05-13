from django.db import models


class Reunion(models.Model):

    debut = models.DateTimeField()
    fin = models.DateTimeField(null=True, blank=True)

    organe = models.ForeignKey(
        'Organe',
        on_delete=models.CASCADE,
    )

    adresse = models.ForeignKey(
        'Adresse',
        on_delete=models.SET_NULL,
        null=True,
    )

    membres = models.ManyToManyField(
        'Membre',
        through='MembreReunion',
    )

    @property
    def date_debut(self):
        return self.debut.date()


    def __str__(self):
        return f'{self.organe} - {self.date_debut}'