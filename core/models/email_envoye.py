from django.db import models


class EmailEnvoye(models.Model):
    reunion = models.ForeignKey('Reunion', on_delete=models.CASCADE, related_name='emails_envoyes')
    envoye_le = models.DateTimeField(auto_now_add=True)
    sujet = models.CharField(max_length=255)
    corps = models.TextField()
    destinataires = models.JSONField()
    reply_to = models.EmailField(blank=True)

    class Meta:
        verbose_name = 'Email envoyé'
        verbose_name_plural = 'Emails envoyés'
        ordering = ['-envoye_le']

    def __str__(self):
        return f'{self.sujet} ({self.envoye_le:%d/%m/%Y %H:%M})'