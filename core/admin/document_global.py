import io
import zipfile

from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from core.models import DocumentReunion


@admin.register(DocumentReunion)
class DocumentGlobalAdmin(ModelAdmin):
    list_display = ['nom', 'annee', 'fichier', 'public', 'lien_public']
    list_filter = [
        'annee',
        'reunion'
    ]
    list_filter_submit = True
    fields = ['nom', 'reunion', 'annee', 'fichier', 'public', 'lien_public']
    readonly_fields = ['lien_public']
    actions = ['telecharger_zip']

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.reunion_id:
            return [*self.readonly_fields, 'annee']
        return self.readonly_fields

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

    @admin.action(description='Télécharger les documents (ZIP)')
    def telecharger_zip(self, request, queryset):
        docs = queryset.exclude(fichier='').select_related('reunion__organe')
        annees = {doc.annee for doc in docs}
        filename = f'documents_{annees.pop()}.zip' if len(annees) == 1 else 'documents.zip'

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for doc in docs:
                dossier = str(doc.annee or 'Sans année')
                if doc.reunion:
                    organe = doc.reunion.organe
                    dossier += (
                        f"/{organe.nom}/"
                        f"{doc.reunion.debut.strftime('%Y-%m-%d')} - {organe.nom_court or organe.nom}"
                    )
                else:
                    dossier += '/Documents généraux'
                nom_fichier = doc.nom or doc.fichier.name.split('/')[-1]
                try:
                    with doc.fichier.open('rb') as f:
                        zf.writestr(f"{dossier}/{nom_fichier}", f.read())
                except FileNotFoundError:
                    pass
        buf.seek(0)
        response = HttpResponse(buf, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
