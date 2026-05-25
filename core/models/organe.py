from django.db import models


class Organe(models.Model):

    code = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=255)

    nom_court = models.CharField(max_length=100, blank=True, null=True)

    preposition = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Préposition à utiliser devant le nom dans les documents (ex: \"au\", \"à l'\", \"à la\").",
    )

    duree_mandat = models.PositiveIntegerField(default=0, help_text="Durée par défaut d'un mandat, en années (0 = pas de date de fin)")

    membres = models.ManyToManyField(
        'Membre',
        through='Adhesion',
    )

    def __str__(self):
        return self.nom