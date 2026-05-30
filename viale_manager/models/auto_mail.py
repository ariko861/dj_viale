from django.db import models


class AutoMails(models.Model):

    class TypeAutoMail(models.TextChoices):
        ARRIVAL = 'arrival', "Arrivée — relatif à la date d'arrivée (décalage en jours)"
        CONFIRMATION = 'confirmation', "Confirmation — envoyé à la confirmation de la réservation"

    id = models.BigAutoField(primary_key=True)
    sujet = models.CharField(max_length=255)
    body = models.TextField(help_text='Contenu HTML de l\'email.')
    type = models.CharField(max_length=255, choices=TypeAutoMail.choices)
    time_delta = models.IntegerField(
        blank=True, null=True,
        verbose_name='décalage (jours)',
        help_text="Nombre de jours d'écart avec l'évènement visé "
                  "(négatif = avant, positif = après).",
        db_comment="donne le nombre de jour de différence avec l'évènement visé",
    )
    actif = models.BooleanField(default=False)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.sujet

    class Meta:
        db_table = '"viale_manager"."auto_mails"'
        verbose_name = 'email automatique'
        verbose_name_plural = 'emails automatiques'