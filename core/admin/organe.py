from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from core.models import Organe


class MembresInline(TabularInline):
    model = Organe.membres.through
    extra = 0
    tab = True


@admin.register(Organe)
class OrganeAdmin(ModelAdmin):

    inlines = [MembresInline]