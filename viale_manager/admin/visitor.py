from collections import defaultdict

from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.db.models import Count, F, Max, Window
from django.db.models.functions import Lower, Trim
from django.template.response import TemplateResponse
from unfold.admin import ModelAdmin, TabularInline

from viale_manager.models import VisitorContacts, Visitors
from .site import viale_admin


def _cle_doublon(v):
    return (v.nom.strip().lower(), v.prenom.strip().lower(), v.date_de_naissance)


class DoublonsFilter(admin.SimpleListFilter):
    title = 'Doublons probables'
    parameter_name = 'doublons'

    def lookups(self, request, model_admin):
        return [
            ('naissance', 'Même nom, prénom et naissance'),
            ('nom', 'Même nom et prénom'),
        ]

    def queryset(self, request, queryset):
        partition = [Lower(Trim('nom')), Lower(Trim('prenom'))]
        match self.value():
            case 'naissance':
                queryset = queryset.exclude(date_de_naissance__isnull=True)
                partition.append(F('date_de_naissance'))
            case 'nom':
                pass
            case _:
                return queryset
        return queryset.annotate(
            n_doublons=Window(Count('id'), partition_by=partition),
        ).filter(n_doublons__gt=1)


class VisitorContactsInline(TabularInline):
    model = VisitorContacts
    fields = ['type', 'value']
    extra = 0


class VisitorAdmin(ModelAdmin):
    search_fields = ['nom', 'prenom', 'email', 'phone', 'contacts__value']
    inlines = [VisitorContactsInline]
    list_display = ['nom', 'prenom', 'date_de_naissance', 'email', 'phone', 'nb_sejours', 'confirmed']
    list_filter = [DoublonsFilter, 'confirmed']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['fusionner', 'fusionner_doublons_evidents']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            sejours_count=Count('sejours', distinct=True), dernier_sejour=Max('sejours__arrival_date'),
        )

    @admin.display(description='séjours', ordering='sejours_count')
    def nb_sejours(self, obj):
        return obj.sejours_count

    @admin.action(description='Fusionner les visiteurs sélectionnés', permissions=['delete'])
    def fusionner(self, request, queryset):
        visitors = list(queryset.order_by(F('dernier_sejour').desc(nulls_last=True), '-id'))
        if len(visitors) < 2:
            self.message_user(request, "Sélectionnez au moins deux visiteurs.", messages.WARNING)
            return None

        if request.POST.get('apply'):
            reference = next((v for v in visitors if str(v.pk) == request.POST.get('reference')), None)
            if reference is None:
                self.message_user(request, "Choisissez la fiche à conserver.", messages.ERROR)
            else:
                n = reference.absorb(visitors)
                self.message_user(request, f"{n} fiche(s) fusionnée(s) dans {reference}.", messages.SUCCESS)
                return None

        request.current_app = self.admin_site.name
        return TemplateResponse(request, 'viale_manager/admin/visitors_merge.html', {
            **self.admin_site.each_context(request),
            'title': 'Fusionner des visiteurs',
            'opts': self.model._meta,
            'visitors': visitors,
            'action': 'fusionner',
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'select_across': request.POST.get('select_across') == '1',
        })

    @admin.action(description='Fusionner les doublons évidents (nom, prénom, naissance)', permissions=['delete'])
    def fusionner_doublons_evidents(self, request, queryset):
        """Regroupe la sélection par nom + prénom + naissance et fusionne chaque groupe.

        La fiche conservée est celle du séjour le plus récent (à défaut, la plus
        récente), supposée avoir les coordonnées les plus à jour.
        """
        groupes = defaultdict(list)
        for v in queryset.exclude(date_de_naissance__isnull=True).order_by(F('dernier_sejour').desc(nulls_last=True), '-id'):
            groupes[_cle_doublon(v)].append(v)
        groupes = [g for g in groupes.values() if len(g) > 1]

        if request.POST.get('apply'):
            n = sum(g[0].absorb(g[1:]) for g in groupes)
            self.message_user(
                request, f"{len(groupes)} visiteur(s) dédoublonné(s), {n} fiche(s) supprimée(s).", messages.SUCCESS,
            )
            return None

        if not groupes:
            self.message_user(request, "Aucun doublon évident dans la sélection.", messages.INFO)
            return None
        request.current_app = self.admin_site.name
        return TemplateResponse(request, 'viale_manager/admin/visitors_merge_obvious.html', {
            **self.admin_site.each_context(request),
            'title': 'Fusionner les doublons évidents',
            'opts': self.model._meta,
            'groupes': groupes,
            'nb_fiches': sum(len(g) - 1 for g in groupes),
            'selected': queryset.values_list('pk', flat=True),
            'action': 'fusionner_doublons_evidents',
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'select_across': request.POST.get('select_across') == '1',
        })


viale_admin.register(Visitors, VisitorAdmin)
