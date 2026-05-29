from django.db import models


class Messages(models.Model):
    id = models.BigAutoField(primary_key=True)
    message = models.TextField()
    type = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    title = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'messages'
