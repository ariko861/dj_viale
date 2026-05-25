from django.contrib import admin
from unfold.admin import ModelAdmin

from core.models import Adresse


@admin.register(Adresse)
class AdresseAdmin(ModelAdmin):
    list_filter = ['est_lieu_reunion']