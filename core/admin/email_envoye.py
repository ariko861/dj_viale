from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from core.models import EmailEnvoye


@admin.register(EmailEnvoye)
class EmailEnvoyeAdmin(ModelAdmin):
    list_display = ['envoye_le', 'sujet', 'reunion', 'destinataires_liste']
    list_filter = ['reunion']
    readonly_fields = ['envoye_le', 'reunion', 'sujet', 'corps_rendu', 'destinataires_liste', 'reply_to']
    fields = ['envoye_le', 'reunion', 'sujet', 'reply_to', 'destinataires_liste', 'corps_rendu']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def destinataires_liste(self, obj):
        return ', '.join(obj.destinataires)

    destinataires_liste.short_description = 'Destinataires'

    def corps_rendu(self, obj):
        return format_html(
            '<div style="border:1px solid #e5e7eb; border-radius:6px; padding:16px; background:#fff;">{}</div>',
            obj.corps,
        )

    corps_rendu.short_description = 'Corps'