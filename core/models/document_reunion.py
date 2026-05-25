import uuid

from django.db import models


class DocumentReunion(models.Model):
    reunion = models.ForeignKey('Reunion', on_delete=models.CASCADE, related_name='documents')
    nom = models.CharField(max_length=255, blank=True)
    fichier = models.FileField(upload_to='documents/reunions/')
    public = models.BooleanField(
        default=False,
        help_text="Si coché, le document est accessible via un lien sans authentification.",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['nom']

    def __str__(self):
        return self.nom or self.fichier.name
