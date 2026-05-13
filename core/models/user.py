from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    membre = models.OneToOneField(
        'Membre',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )