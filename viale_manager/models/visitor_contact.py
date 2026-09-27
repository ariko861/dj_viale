from django.db import models


class VisitorContacts(models.Model):
    """Coordonnée secondaire d'un visiteur (la principale reste sur ``Visitors``).

    Une même valeur peut appartenir à plusieurs visiteurs : une famille partage
    souvent l'adresse d'un parent.
    """

    class Type(models.TextChoices):
        EMAIL = 'email', 'Email'
        PHONE = 'phone', 'Téléphone'

    id = models.BigAutoField(primary_key=True)
    visitor = models.ForeignKey('Visitors', models.CASCADE, related_name='contacts')
    type = models.CharField(max_length=10, choices=Type.choices)
    value = models.CharField(max_length=255, verbose_name='valeur')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.value

    class Meta:
        db_table = '"viale_manager"."visitor_contacts"'
        verbose_name = 'autre coordonnée'
        verbose_name_plural = 'autres coordonnées'
        constraints = [
            models.UniqueConstraint(fields=['visitor', 'type', 'value'], name='visitor_contact_unique'),
        ]
