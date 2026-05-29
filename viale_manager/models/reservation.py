from django.db import models


class Reservations(models.Model):
    id = models.BigAutoField(primary_key=True)
    authorize_edition = models.BooleanField()
    link_token = models.UUIDField(unique=True)
    max_days_change = models.IntegerField()
    max_visitors = models.IntegerField()
    remarques_visiteur = models.TextField(blank=True, null=True)
    remarques_accueil = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    link_sent = models.BooleanField()
    contact_email = models.CharField(max_length=255, blank=True, null=True)
    contact_phone = models.CharField(max_length=255, blank=True, null=True)
    all_mails_required = models.BooleanField()
    groupe = models.BooleanField(db_comment='Est-ce une réservation pour un groupe, active formulaire simplifié')
    nom_groupe = models.CharField(max_length=255, blank=True, null=True, db_comment='Nom du groupe')

    class Meta:
        db_table = '"viale_manager"."reservations"'
