from collections import defaultdict

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.db.models import Count, F, Max, Q, Window
from django.db.models.functions import ExtractYear, Lower, Trim
from django.template.response import TemplateResponse
from unfold.admin import ModelAdmin, TabularInline

from viale_manager.forms import EnvoiEmailForm
from viale_manager.mailing import send_message
from viale_manager.models import VisitorContacts, Visitors
from viale_manager.models.visitor import FusionImpossible
from .site import viale_admin


def _cle_doublon(v):
    return (v.nom.strip().lower(), v.prenom.strip().lower(), v.date_de_naissance)


def _au_1er_janvier(d):
    return (d.month, d.day) == (1, 1)


class DoublonsFilter(admin.SimpleListFilter):
    title = 'Doublons probables'
    parameter_name = 'doublons'

    def lookups(self, request, model_admin):
        lookups = [
            ('naissance', 'Même nom, prénom et naissance'),
            ('nom', 'Même nom et prénom'),
        ]
        if settings.VIALE_FUSION_1ER_JANVIER:
            lookups.append(('1er_janvier', 'Même nom, prénom et année, dont un 1er janvier'))
        return lookups

    def queryset(self, request, queryset):
        partition = [Lower(Trim('nom')), Lower(Trim('prenom'))]
        match self.value():
            case 'naissance':
                queryset = queryset.exclude(date_de_naissance__isnull=True)
                partition.append(F('date_de_naissance'))
            case 'nom':
                pass
            case '1er_janvier' if settings.VIALE_FUSION_1ER_JANVIER:
                partition.append(ExtractYear('date_de_naissance'))
                return queryset.exclude(date_de_naissance__isnull=True).annotate(
                    n_doublons=Window(Count('id'), partition_by=partition),
                    n_1er_janvier=Window(
                        Count('id', filter=Q(date_de_naissance__month=1, date_de_naissance__day=1)),
                        partition_by=partition,
                    ),
                ).filter(n_doublons__gt=1, n_1er_janvier__gt=0)
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
    actions = ['envoyer_email', 'fusionner', 'fusionner_doublons_evidents', 'fusionner_doublons_1er_janvier']

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not settings.VIALE_FUSION_1ER_JANVIER:
            actions.pop('fusionner_doublons_1er_janvier', None)
        return actions

    def get_readonly_fields(self, request, obj=None):
        # Attribuer un compte donne accès aux séjours de la fiche : réservé aux superusers.
        readonly = super().get_readonly_fields(request, obj)
        return readonly if request.user.is_superuser else [*readonly, 'user']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            sejours_count=Count('sejours', distinct=True), dernier_sejour=Max('sejours__arrival_date'),
        )

    @admin.display(description='séjours', ordering='sejours_count')
    def nb_sejours(self, obj):
        return obj.sejours_count

    @admin.action(description='Envoyer un email', permissions=['change'])
    def envoyer_email(self, request, queryset):
        """Email libre aux visiteurs sélectionnés : une page demande le sujet et le message."""
        visitors = list(queryset)
        adresses = {v.email.strip().lower() for v in visitors if v.email and v.email.strip()}
        sans_email = sum(1 for v in visitors if not (v.email and v.email.strip()))

        form = EnvoiEmailForm(request.POST if request.POST.get('apply') else None)
        if form.is_valid():
            envoyes, echecs = send_message(adresses, form.cleaned_data['sujet'], form.cleaned_data['message'])
            self.message_user(request, f"Email envoyé à {envoyes} adresse(s).", messages.SUCCESS)
            if sans_email:
                self.message_user(request, f"{sans_email} visiteur(s) sans email ignoré(s).", messages.WARNING)
            if echecs:
                self.message_user(
                    request, f"Échec de l'envoi à {len(echecs)} adresse(s) : {', '.join(echecs)}.", messages.ERROR,
                )
            return None

        request.current_app = self.admin_site.name
        return TemplateResponse(request, 'viale_manager/admin/visitors_email.html', {
            **self.admin_site.each_context(request),
            'title': 'Envoyer un email',
            'opts': self.model._meta,
            'form': form,
            'nb_visiteurs': len(visitors),
            'nb_adresses': len(adresses),
            'sans_email': sans_email,
            'action': 'envoyer_email',
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'select_across': request.POST.get('select_across') == '1',
            'selected': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
        })

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
                try:
                    n = reference.absorb(visitors)
                except FusionImpossible as e:
                    self.message_user(request, str(e), messages.ERROR)
                    return None
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
            # Django ignore la confirmation sans au moins un id coché, même en select_across.
            'selected': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
        })

    @admin.action(description='Fusionner les doublons évidents (nom, prénom, naissance)', permissions=['delete'])
    def fusionner_doublons_evidents(self, request, queryset):
        """Regroupe la sélection par nom + prénom + naissance et fusionne chaque groupe.

        La fiche conservée est celle du séjour le plus récent (à défaut, la plus
        récente), supposée avoir les coordonnées les plus à jour. Les groupes où
        plusieurs fiches ont un compte visiteur sont écartés (cf.
        :class:`~viale_manager.models.visitor.FusionImpossible`).
        """
        groupes = defaultdict(list)
        for v in queryset.exclude(date_de_naissance__isnull=True).order_by(F('dernier_sejour').desc(nulls_last=True), '-id'):
            groupes[_cle_doublon(v)].append(v)
        groupes = [g for g in groupes.values() if len(g) > 1]
        return self._fusionner_groupes(request, groupes, 'fusionner_doublons_evidents', 'Fusionner les doublons évidents')

    @admin.action(description='Fusionner les doublons au 1er janvier (nom, prénom, année)', permissions=['delete'])
    def fusionner_doublons_1er_janvier(self, request, queryset):
        """Nettoyage des fiches héritées de l'ancienne application, nées « au 1er janvier ».

        Regroupe la sélection par nom + prénom + année de naissance ; un groupe
        est fusionné s'il compte au moins une fiche au 1er janvier et au plus une
        autre date de naissance, que la fiche conservée reprend. Deux dates
        précises différentes désignent deux personnes : le groupe est écarté.
        Activée par le réglage ``VIALE_FUSION_1ER_JANVIER``.
        """
        groupes = defaultdict(list)
        for v in queryset.exclude(date_de_naissance__isnull=True).order_by(F('dernier_sejour').desc(nulls_last=True), '-id'):
            groupes[(v.nom.strip().lower(), v.prenom.strip().lower(), v.date_de_naissance.year)].append(v)
        groupes = [
            g for g in groupes.values()
            if len(g) > 1 and any(_au_1er_janvier(v.date_de_naissance) for v in g)
        ]
        ambigus = [
            g for g in groupes
            if len({v.date_de_naissance for v in g if not _au_1er_janvier(v.date_de_naissance)}) > 1
        ]
        if ambigus:
            self.message_user(
                request,
                f"{len(ambigus)} groupe(s) écarté(s), plusieurs dates de naissance précises : "
                + ' ; '.join(str(g[0]) for g in ambigus) + ". À fusionner à la main après vérification.",
                messages.WARNING,
            )
        groupes = [g for g in groupes if g not in ambigus]
        for g in groupes if request.POST.get('apply') else []:
            # absorb() garde la date de la fiche conservée : on lui donne la date précise.
            g[0].date_de_naissance = next(
                (v.date_de_naissance for v in g if not _au_1er_janvier(v.date_de_naissance)), g[0].date_de_naissance,
            )
        return self._fusionner_groupes(
            request, groupes, 'fusionner_doublons_1er_janvier', 'Fusionner les doublons au 1er janvier',
        )

    def _fusionner_groupes(self, request, groupes, action, title):
        """Confirme puis fusionne chaque groupe dans sa première fiche.

        Les groupes où plusieurs fiches ont un compte visiteur sont écartés (cf.
        :class:`~viale_manager.models.visitor.FusionImpossible`).

        :param groupes: listes de visiteurs, la fiche à conserver en premier.
        :param action: nom de l'action admin, reposté par la page de confirmation.
        :param title: titre de la page de confirmation.
        """
        avec_comptes = [g for g in groupes if sum(1 for v in g if v.user_id) > 1]
        groupes = [g for g in groupes if g not in avec_comptes]
        if avec_comptes:
            self.message_user(
                request,
                f"{len(avec_comptes)} groupe(s) écarté(s), plusieurs fiches ayant un compte visiteur : "
                + ' ; '.join(str(g[0]) for g in avec_comptes) + ". À fusionner à la main après vérification.",
                messages.WARNING,
            )

        if request.POST.get('apply'):
            n = sum(g[0].absorb(g[1:]) for g in groupes)
            self.message_user(
                request, f"{len(groupes)} visiteur(s) dédoublonné(s), {n} fiche(s) supprimée(s).", messages.SUCCESS,
            )
            return None

        if not groupes:
            self.message_user(request, "Aucun doublon dans la sélection.", messages.INFO)
            return None
        request.current_app = self.admin_site.name
        return TemplateResponse(request, 'viale_manager/admin/visitors_merge_obvious.html', {
            **self.admin_site.each_context(request),
            'title': title,
            'opts': self.model._meta,
            'groupes': groupes,
            'nb_fiches': sum(len(g) - 1 for g in groupes),
            'action': action,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'select_across': request.POST.get('select_across') == '1',
            # Django ignore la confirmation sans au moins un id coché, même en select_across.
            'selected': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
        })

viale_admin.register(Visitors, VisitorAdmin)
