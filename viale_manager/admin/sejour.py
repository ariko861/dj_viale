from unfold.admin import ModelAdmin, TabularInline

from viale_manager.models import Reservations, Sejours
from .site import viale_admin


class SejoursInline(TabularInline):
    model = Sejours
    extra = 0
    tab = True
    fields = ['visitor', 'room', 'arrival_date', 'departure_date', 'price', 'confirmed']
    autocomplete_fields = ['visitor', 'room']


class SejourAdmin(ModelAdmin):
    list_display = ['visitor', 'arrival_date', 'departure_date', 'room', 'price', 'confirmed']
    list_filter = ['confirmed', 'arrival_date', 'remove_from_stats']
    search_fields = ['visitor__nom', 'visitor__prenom']
    autocomplete_fields = ['visitor', 'room', 'reservation']
    date_hierarchy = 'arrival_date'
    readonly_fields = ['created_at', 'updated_at']


class ReservationAdmin(ModelAdmin):
    list_display = ['id', 'contact_email', 'contact_phone', 'confirmed_at', 'link_sent', 'groupe', 'nom_groupe']
    list_filter = ['link_sent', 'groupe', 'all_mails_required']
    search_fields = ['contact_email', 'contact_phone', 'nom_groupe']
    readonly_fields = ['created_at', 'updated_at', 'confirmed_at', 'link_token']
    inlines = [SejoursInline]


viale_admin.register(Sejours, SejourAdmin)
viale_admin.register(Reservations, ReservationAdmin)