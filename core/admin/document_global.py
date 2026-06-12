from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from core.models import DocumentReunion


@admin.register(DocumentReunion)
class DocumentGlobalAdmin(ModelAdmin):
    list_display = ['nom', 'fichier', 'public', 'lien_public']
    list_filter = [
        'reunion'
    ]
    list_filter_submit = True
    fields = ['nom', 'fichier', 'public', 'lien_public']
    readonly_fields = ['lien_public']

    def changeform_view(self, request, *args, **kwargs):
        self._request = request
        return super().changeform_view(request, *args, **kwargs)

    def lien_public(self, obj):
        if not obj.pk or not obj.public:
            return '—'
        request = getattr(self, '_request', None)
        if not request:
            return '—'
        url = request.build_absolute_uri(reverse('document-reunion', args=[obj.token]))
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)

    lien_public.short_description = 'Lien public'