from datetime import timedelta

from constance import config
from django.db import models
from django.utils import timezone


class Reservations(models.Model):
    id = models.BigAutoField(primary_key=True)
    authorize_edition = models.BooleanField()
    link_token = models.UUIDField(unique=True)
    max_days_change = models.IntegerField()
    max_visitors = models.IntegerField()
    remarques_visiteur = models.TextField(blank=True, null=True)
    remarques_accueil = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    link_valid_from = models.DateTimeField(
        blank=True, null=True,
        help_text="Départ de la validité du lien (création ou dernier envoi) ; à défaut, la création.",
    )
    link_sent = models.BooleanField()
    contact_email = models.CharField(max_length=255, blank=True, null=True)
    contact_phone = models.CharField(max_length=255, blank=True, null=True)
    all_mails_required = models.BooleanField()
    groupe = models.BooleanField(db_comment='Est-ce une réservation pour un groupe, active formulaire simplifié')
    nom_groupe = models.CharField(max_length=255, blank=True, null=True, db_comment='Nom du groupe')

    @property
    def lien_expire(self) -> bool:
        """Lien non confirmé plus vieux que ``VIALE_LIEN_VALIDITE_JOURS`` : il ne peut plus servir."""
        depart = self.link_valid_from or self.created_at
        if self.confirmed_at or depart is None:
            return False
        return timezone.now() > depart + timedelta(days=config.VIALE_LIEN_VALIDITE_JOURS)

    @property
    def color(self) -> str:
        hue = self.link_token.int % 360
        return f'hsl({hue}, 55%, 78%)'

    class Meta:
        db_table = '"viale_manager"."reservations"'
        verbose_name = 'réservation'
