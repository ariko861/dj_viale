import uuid

from django.db import models


class DocumentReunion(models.Model):
    reunion = models.ForeignKey(
        'Reunion', on_delete=models.CASCADE, related_name='documents',
        null=True, blank=True,
    )
    annee = models.PositiveSmallIntegerField(
        'année',
        null=True,
        blank=True,
        db_index=True,
        help_text="Reprise automatiquement de la réunion si le document y est lié.",
    )
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

    def save(self, *args, **kwargs):
        if self.reunion_id:
            self.annee = self.reunion.annee
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom or self.fichier.name
