from django.db import models


class ModeleDocument(models.Model):

    nom = models.CharField(max_length=255)

    tag = models.ForeignKey(
        'TagDocument',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modeles',
    )

    fichier = models.FileField(upload_to='modeles_documents/')

    organes = models.ManyToManyField(
        'Organe',
        related_name='modeles_documents',
        blank=True,
    )

    def __str__(self):
        return self.nom