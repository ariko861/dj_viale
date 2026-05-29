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

    confirmed = models.BooleanField(verbose_name="confirmé", default=False)
    remove_from_stats = models.BooleanField(verbose_name="retirer des statistiques", default=False)
    arrival_date = models.DateField(verbose_name="date d'arrivée")
    departure_date = models.DateField(blank=True, null=True, verbose_name="date de départ")
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    room = models.ForeignKey('Rooms', models.SET_NULL, blank=True, null=True)

    price = models.FloatField(blank=True, null=True, verbose_name="prix")


    @property
    def nuitees(self) -> int | None:
        if self.departure_date is None:
            return None
        return (self.departure_date - self.arrival_date).days


    @property
    def total(self) -> float | None:
        if self.nuitees is None or self.price is None:
            return None
        return self.nuitees * self.price


    def __str__(self):
        return f"{self.visitor} — {self.arrival_date}"

    class Meta:
        db_table = '"viale_manager"."sejours"'
