from django.db import models


class Houses(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    community = models.BooleanField()
    displayhousenamewithroom = models.BooleanField(db_column='displayHouseNameWithRoom', default=False)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = '"viale_manager"."houses"'
