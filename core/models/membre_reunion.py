from django.db import models


class MembreReunion(models.Model):

    membre = models.ForeignKey(
        'Membre',
        on_delete=models.CASCADE,
    )

    reunion = models.ForeignKey(
        'Reunion',
        on_delete=models.CASCADE,
    )

    class Statut(models.TextChoices):
        MEMBRE_OFFICIEL = 'MO', 'Membre officiel'
        INVITE = 'I', 'Invité'

    statut = models.CharField(
        max_length=2,
        choices=Statut.choices,
        default=Statut.MEMBRE_OFFICIEL,
    )

    class Etat(models.TextChoices):
        INVITE = 'I', 'Invité'
        ACCEPTE = 'A', 'Accepté'
        ABSENT = 'AB', 'Absent'
        PROCURATION = 'P', 'Procuration'

    etat = models.CharField(
        max_length=2,
        choices=Etat.choices,
        default=Etat.INVITE,
    )
