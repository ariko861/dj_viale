from django.db import models


class AutoMails(models.Model):
    id = models.BigAutoField(primary_key=True)
    sujet = models.CharField(max_length=255)
    body = models.TextField()
    type = models.CharField(max_length=255)
    time_delta = models.IntegerField(blank=True, null=True, db_comment="donne le nombre de jour de différence avec l'évènement visé")
    actif = models.BooleanField()
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta:
        db_table = '"viale_manager"."auto_mails"'