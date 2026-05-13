from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, StackedInline
from unfold.decorators import action

from core.models import Reunion


class MembresInline(StackedInline):
    model = Reunion.membres.through
    extra = 0
    tab = True


@admin.register(Reunion)
class ReunionAdmin(ModelAdmin):

    inlines = [MembresInline]
    actions_detail = ['telecharger_ical']

    @action(description='Télécharger iCal', url_path='ical')
    def telecharger_ical(self, request, object_id):
        from django.shortcuts import redirect
        return redirect(reverse('reunion-ical', args=[object_id]))