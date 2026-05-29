from django.db import models

from .house import Houses


class Rooms(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)

    house = models.ForeignKey(
        'Houses',
        models.SET_NULL,
        blank=True, null=True
    )
    beds = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = '"viale_manager"."rooms"'
