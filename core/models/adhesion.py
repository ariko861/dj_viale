from datetime import date

from django.db import models


class Adhesion(models.Model):

    class Statut(models.TextChoices):
        MEMBRE_OFFICIEL = 'MO', 'Membre officiel'
        INVITE_PERMANENT = 'IP', 'Invité permanent'

    statut = models.CharField(
        max_length=2,
        choices=Statut.choices,
        default=Statut.MEMBRE_OFFICIEL,
    )

    debut = models.DateField(null=True, default=date.today)
    fin = models.DateField(null=True, blank=True)

    organe = models.ForeignKey(
        'Organe',
        on_delete=models.CASCADE
    )

    membre = models.ForeignKey(
        'Membre',
        on_delete=models.CASCADE
    )

    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.debut} - {self.membre}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['organe', 'membre'], name='unique_adhesion_organe_membre')
        ]