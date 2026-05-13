from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline

from core.models import Organe


class MembresInline(StackedInline):
    model = Organe.membres.through
    extra = 0
    tab = True


@admin.register(Organe)
class OrganeAdmin(ModelAdmin):

    inlines = [MembresInline]