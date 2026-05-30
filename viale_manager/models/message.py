from django.db import models


class Messages(models.Model):

    class TypeMessage(models.TextChoices):
        LINK = 'link', 'Lien — affiché au début du formulaire'
        CONFIRMATION = 'confirmation', 'Confirmation — affiché à la fin du formulaire'

    id = models.BigAutoField(primary_key=True)
    message = models.TextField(help_text='Contenu HTML affiché dans le formulaire de réservation.')
    type = models.CharField(max_length=255, choices=TypeMessage.choices)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title or f'Message #{self.pk}'

    class Meta:
        db_table = '"viale_manager"."messages"'
        verbose_name = 'message'
