import io
import zipfile

from constance import config
from django.contrib import admin, messages
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html, mark_safe
from docxtpl import DocxTemplate
from icalendar import Calendar, Event
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action

from core.forms import EnvoyerEmailForm
from core.models import DocumentReunion, Membre, ModeleDocument, Procuration, Reunion


class DocumentsInline(TabularInline):
    model = DocumentReunion
    extra = 0
    tab = True
    fields = ['nom', 'fichier', 'public', 'lien_public']
    readonly_fields = ['lien_public']

    def get_formset(self, request, obj=None, **kwargs):
        self._request = request
        return super().get_formset(request, obj, **kwargs)

    def lien_public(self, obj):
        if not obj.pk or not obj.public:
            return '—'
        url = self._request.build_absolute_uri(reverse('document-reunion', args=[obj.token]))
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)

    lien_public.short_description = 'Lien public'


class MembresInline(TabularInline):
    model = Reunion.membres.through
    extra = 0
    tab = True


class ProcurationsInline(TabularInline):
    model = Procuration
    extra = 0
    tab = True

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj and obj.pk:
            membres_qs = Membre.objects.filter(membrereunion__reunion=obj)
            formset.form.base_fields['mandant'].queryset = membres_qs
            formset.form.base_fields['mandataire'].queryset = membres_qs
        return formset


@admin.register(Reunion)
class ReunionAdmin(ModelAdmin):

    inlines = [DocumentsInline, MembresInline, ProcurationsInline]
    readonly_fields = ['documents_disponibles']
    actions_detail = ['telecharger_ical', 'envoyer_email', 'telecharger_documents_zip']
    actions = ['telecharger_documents_zip_action']


    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<int:pk>/email/',
                self.admin_site.admin_view(self.envoyer_email_view),
                name='core_reunion_email',
            ),
        ]
        return custom + urls

    def documents_disponibles(self, obj):
        if not obj.pk:
            return '—'
        modeles = ModeleDocument.objects.filter(organes=obj.organe).select_related('tag')
        if not modeles:
            return 'Aucun document configuré pour cet organe.'
        links = [
            format_html(
                '<a href="{}" class="mr-2">[{}] {}</a>',
                reverse('reunion-document', args=[obj.pk, m.pk]),
                m.tag or '—',
                m.nom,
            )
            for m in modeles
        ]
        return mark_safe('<br>'.join(links))

    documents_disponibles.short_description = 'Documents'

    @action(description='Télécharger iCal', url_path='ical')
    def telecharger_ical(self, request, object_id):
        return redirect(reverse('reunion-ical', args=[object_id]))

    @action(description='Télécharger les documents (ZIP)', url_path='zip')
    def telecharger_documents_zip(self, request, object_id):
        reunion = get_object_or_404(Reunion.objects.select_related('organe'), pk=object_id)
        return self._zip_reunions([reunion], f"documents_{reunion.debut.strftime('%Y-%m-%d')}.zip")

    @admin.action(description='Télécharger les documents (ZIP)')
    def telecharger_documents_zip_action(self, request, queryset):
        reunions = queryset.select_related('organe').prefetch_related('documents')
        return self._zip_reunions(list(reunions), 'documents.zip')

    def _zip_reunions(self, reunions, filename):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for reunion in reunions:
                dossier = (
                    f"{reunion.organe.nom}/"
                    f"{reunion.debut.strftime('%Y-%m-%d')} - {reunion.organe.nom_court or reunion.organe.nom}"
                )
                docs = DocumentReunion.objects.filter(reunion=reunion).exclude(fichier='')
                for doc in docs:
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

    @action(description='Envoyer un email', url_path='email')
    def envoyer_email(self, request, object_id):
        return redirect(reverse('admin:core_reunion_email', args=[object_id]))

    def envoyer_email_view(self, request, pk):
        reunion = get_object_or_404(
            Reunion.objects.select_related('organe', 'adresse'),
            pk=pk,
        )

        if request.method == 'POST':
            form = EnvoyerEmailForm(request.POST, reunion=reunion)
            if form.is_valid():
                destinataires = [m.email for m in form.cleaned_data['destinataires']]
                reply_to_value = form.cleaned_data.get('reply_to')
                email = EmailMessage(
                    subject=form.cleaned_data['sujet'],
                    body=form.cleaned_data['corps'],
                    to=destinataires,
                    reply_to=[reply_to_value] if reply_to_value else [],
                )
                email.content_subtype = 'html'

                if form.cleaned_data.get('joindre_ical'):
                    email.attach(
                        f"reunion-{reunion.pk}.ics",
                        self._generer_ical(reunion),
                        'text/calendar',
                    )

                for modele in form.cleaned_data['documents']:
                    contenu = self._generer_document(reunion, modele)
                    nom = f"{modele.nom} - {reunion.debut.strftime('%Y-%m-%d')}.docx"
                    email.attach(
                        nom,
                        contenu,
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    )

                for doc in form.cleaned_data['documents_reunion']:
                    with doc.fichier.open('rb') as f:
                        email.attach(
                            doc.fichier.name.split('/')[-1],
                            f.read(),
                            'application/octet-stream',
                        )

                email.send()
                messages.success(request, f'Email envoyé à {len(destinataires)} destinataire(s).')
                return redirect(reverse('admin:core_reunion_change', args=[pk]))
        else:
            form = EnvoyerEmailForm(
                reunion=reunion,
                initial={
                    'destinataires': list(reunion.membres.values_list('pk', flat=True)),
                    'sujet': f'[{reunion.organe}] {reunion.debut.strftime("%d/%m/%Y")}',
                    'reply_to': config.REPLY_TO_EMAIL,
                    'joindre_ical': True,
                },
            )

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'reunion': reunion,
            'form': form,
            'title': 'Envoyer un email',
        }
        return render(request, 'admin/core/reunion/envoyer_email.html', context)

    def _generer_ical(self, reunion):
        cal = Calendar()
        cal.add('prodid', '-//dj-asbl//FR')
        cal.add('version', '2.0')
        event = Event()
        event.add('summary', str(reunion))
        event.add('dtstart', reunion.debut)
        event.add('dtend', reunion.fin or reunion.debut)
        event.add('uid', f'reunion-{reunion.pk}@dj-asbl')
        if reunion.adresse:
            location = f"{reunion.adresse.adresse}, {reunion.adresse.code_postal} {reunion.adresse.ville}"
            event.add('location', location)
        cal.add_component(event)
        return cal.to_ical()

    def _generer_document(self, reunion, modele):
        membres = (
            reunion.membrereunion_set
            .select_related('membre')
            .order_by('membre__nom', 'membre__prenom')
        )
        context = {
            'reunion': reunion,
            'organe': reunion.organe,
            'adresse': reunion.adresse,
            'membres': list(membres),
            'date': reunion.debut.strftime('%d/%m/%Y'),
            'heure': reunion.debut.strftime('%H:%M'),
        }
        tpl = DocxTemplate(modele.fichier.path)
        tpl.render(context)
        buf = io.BytesIO()
        tpl.save(buf)
        buf.seek(0)
        return buf.read()