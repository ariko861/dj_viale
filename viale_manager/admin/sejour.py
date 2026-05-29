from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.sections import TemplateSection

from viale_manager.models import Reservations, Sejours
from .site import viale_admin


class PeriodeSejourFilter(admin.SimpleListFilter):
    title = 'Période'
    parameter_name = 'periode'

    def lookups(self, request, model_admin):
        return [
            ('presents',  'Présents en ce moment'),
            ('arrivent',  "Arrivent aujourd'hui"),
            ('partent',   "Partent aujourd'hui"),
            ('futures',   'Arrivées futures'),
            ('termines',  'Séjours terminés'),
        ]

    def queryset(self, request, queryset):
        match self.value():
            case 'presents':  return queryset.presents()
            case 'arrivent':  return queryset.arrivent_aujourd_hui()
            case 'partent':   return queryset.partent_aujourd_hui()
            case 'futures':   return queryset.futurs()
            case 'termines':  return queryset.termines()
        return queryset


class ReservationSection(TemplateSection):
    template_name = 'viale_manager/admin/sections/reservation.html'


class SejourAdmin(ModelAdmin):
    list_display = ['reservation_label', 'visitor', 'arrival_date', 'departure_date', 'nuitees', 'room', 'price', 'confirmed', 'total']
    list_display_links = ['visitor']
    list_filter = [PeriodeSejourFilter, 'confirmed', 'remove_from_stats']
    search_fields = ['visitor__nom', 'visitor__prenom', 'reservation__nom_groupe', 'reservation__contact_email']
    autocomplete_fields = ['room']
    list_select_related = ['visitor', 'room', 'reservation']
    ordering = ['arrival_date', '-reservation_id']
    date_hierarchy = 'arrival_date'
    readonly_fields = ['visitor', 'reservation', 'created_at', 'updated_at']
    list_sections = [ReservationSection]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if 'periode' not in request.GET:
            qs = qs.actifs()
        return qs

    @admin.display(description='', ordering='reservation_id')
    def reservation_label(self, obj):
        color = obj.reservation.color
        return format_html(
            '<span style="display:inline-block;width:16px;height:16px;border-radius:3px;background:{};"></span>',
            color,
        )


class ReservationAdmin(ModelAdmin):
    list_display = ['id', 'contact_email', 'contact_phone', 'confirmed_at', 'link_sent', 'groupe', 'nom_groupe']
    list_filter = ['link_sent', 'groupe', 'all_mails_required']
    search_fields = ['contact_email', 'contact_phone', 'nom_groupe']
    readonly_fields = ['created_at', 'updated_at', 'confirmed_at', 'link_token']

    def has_module_permission(self, request):
        return False


viale_admin.register(Sejours, SejourAdmin)
viale_admin.register(Reservations, ReservationAdmin)