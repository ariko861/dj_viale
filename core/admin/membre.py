from django.contrib import admin
from unfold.admin import ModelAdmin

from core.models import Membre


@admin.register(Membre)
class MembreAdmin(ModelAdmin):
    pass