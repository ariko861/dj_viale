from django.db import models


class Procuration(models.Model):

    mandant = models.ForeignKey(
        'Membre',
        on_delete=models.CASCADE,
        related_name='procurations_donnees',
    )

    mandataire = models.ForeignKey(
        'Membre',
        on_delete=models.CASCADE,
        related_name='procurations_recues',
    )

    reunion = models.ForeignKey(
        'Reunion',
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['mandant', 'reunion'], name='unique_procuration_mandant_reunion')
        ]

    def __str__(self):
        return f"{self.mandant} → {self.mandataire} ({self.reunion})"