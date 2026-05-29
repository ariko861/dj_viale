from django.db import models

from .house import Houses


class Rooms(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name='nom')

    house = models.ForeignKey(
        'Houses',
        models.SET_NULL,
        blank=True, null=True,
        verbose_name='maison',
    )
    beds = models.IntegerField(verbose_name='lit')
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = '"viale_manager"."rooms"'
