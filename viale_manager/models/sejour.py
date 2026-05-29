from django.db import models


class Sejours(models.Model):

    id = models.BigAutoField(primary_key=True)

    reservation = models.ForeignKey(
        'Reservations',
        models.DO_NOTHING
    )

    visitor = models.ForeignKey(
        'Visitors',
        models.CASCADE
    )

    confirmed = models.BooleanField()
    remove_from_stats = models.BooleanField()
    arrival_date = models.DateField()
    departure_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    room = models.ForeignKey('Rooms', models.SET_NULL, blank=True, null=True)

    price = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = '"viale_manager"."sejours"'
