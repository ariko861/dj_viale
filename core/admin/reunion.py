from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.decorators import action

from core.models import Membre, ModeleDocument, Procuration, Reunion


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

    inlines = [MembresInline, ProcurationsInline]
    readonly_fields = ['documents_disponibles']
    actions_detail = ['telecharger_ical']

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
        from django.shortcuts import redirect
        return redirect(reverse('reunion-ical', args=[object_id]))