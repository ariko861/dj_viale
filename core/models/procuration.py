from django.core.exceptions import ValidationError
from django.db import models


class Procuration(models.Model):

    reunion = models.ForeignKey(
        'Reunion',
        on_delete=models.CASCADE,
    )

    mandant = models.OneToOneField(
        'MembreReunion',
        on_delete=models.CASCADE,
        related_name='procuration_donnee',
    )

    mandataire = models.ForeignKey(
        'MembreReunion',
        on_delete=models.CASCADE,
        related_name='procurations_recues',
    )

    fichier = models.FileField(upload_to='procurations/', null=True, blank=True)

    def clean(self):
        errors = {}
        if self.mandant_id and self.reunion_id and self.mandant.reunion_id != self.reunion_id:
            errors['mandant'] = "Le mandant doit appartenir à cette réunion."
        if self.mandataire_id and self.reunion_id and self.mandataire.reunion_id != self.reunion_id:
            errors['mandataire'] = "Le mandataire doit appartenir à cette réunion."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # reunion est dérivable de mandant : on la maintient cohérente automatiquement.
        if not self.reunion_id and self.mandant_id:
            self.reunion_id = self.mandant.reunion_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.mandant.membre} → {self.mandataire.membre} ({self.reunion})"