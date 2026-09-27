import uuid
from datetime import date, timedelta

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action
from unfold.forms import BaseDialogForm
from unfold.sections import TemplateSection

from viale_manager.forms import (
    ReservationAddForm, SejourBreakDialogForm, SejourDatesDialogForm, SejourInlineForm, SejourInlineFormSet,
)
from viale_manager.models import Reservations, Sejours, Visitors
from viale_manager.stats import presences, presences_chart
from .site import viale_admin
from .widgets import reservations_widget_context


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
    change_list_template = 'viale_manager/admin/sejours_change_list.html'

    actions_row = ['action_edit_dates', 'action_add_break', 'action_cancel']

    def _back_to_list(self, request):
        """Réponse d'un dialog htmx : recharge la liste (filtres conservés)."""
        url = request.headers.get('Referer') or reverse('viale_manager:viale_manager_sejours_changelist')
        return HttpResponse(headers={'HX-Redirect': url})

    @action(
        description='Modifier les dates', icon='calendar_month', permissions=['change'],
        dialog={'title': 'Modifier les dates du séjour', 'form_class': SejourDatesDialogForm,
                'form_submit_text': 'Enregistrer'},
    )
    def action_edit_dates(self, request, form, object_id):
        sejour = form.sejour
        sejour.arrival_date = form.cleaned_data['arrival_date']
        sejour.departure_date = form.cleaned_data['departure_date']
        sejour.save(update_fields=['arrival_date', 'departure_date', 'updated_at'])
        messages.success(request, f"Dates du séjour de {sejour.visitor} mises à jour.")
        return self._back_to_list(request)

    @action(
        description='Ajouter une absence', icon='beach_access', permissions=['change'],
        dialog={'title': 'Ajouter une absence',
                'description': "Le séjour est coupé en deux : il se termine au début de l'absence "
                               "et reprend au retour.",
                'form_class': SejourBreakDialogForm, 'form_submit_text': 'Créer'},
    )
    def action_add_break(self, request, form, object_id):
        form.sejour.create_break(form.cleaned_data['begin'], form.cleaned_data['end'])
        messages.success(request, f"Absence ajoutée au séjour de {form.sejour.visitor}.")
        return self._back_to_list(request)

    @action(
        description='Annuler le séjour', icon='cancel', permissions=['delete'],
        dialog={'title': 'Annuler le séjour', 'description': 'Le séjour sera supprimé définitivement.',
                'form_class': BaseDialogForm, 'form_submit_text': 'Annuler le séjour'},
    )
    def action_cancel(self, request, form, object_id):
        sejour = Sejours.objects.select_related('visitor').get(pk=object_id)
        # Un séjour terminé fait partie de l'historique : seul un superuser le supprime.
        if sejour.departure_date and sejour.departure_date < date.today() and not request.user.is_superuser:
            messages.error(request, "Un séjour terminé ne peut pas être annulé.")
        else:
            sejour.delete()
            messages.warning(request, f"Séjour de {sejour.visitor} annulé.")
        return self._back_to_list(request)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if 'periode' not in request.GET:
            qs = qs.actifs()
        return qs

    def changelist_view(self, request, extra_context=None):
        today = date.today()
        jours = presences(today, today + timedelta(days=6))
        chart_data, chart_options = presences_chart(jours)
        extra_context = {
            **(extra_context or {}), **reservations_widget_context(request),
            'jours': jours, 'chart_data': chart_data, 'chart_options': chart_options,
        }
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description='', ordering='reservation_id')
    def reservation_label(self, obj):
        color = obj.reservation.color
        return format_html(
            '<span style="display:inline-block;width:16px;height:16px;border-radius:3px;background:{};"></span>',
            color,
        )


class SejoursInline(TabularInline):
    model = Sejours
    form = SejourInlineForm
    formset = SejourInlineFormSet
    fields = ['visitor', 'profile', 'price', 'arrival_date', 'departure_date']
    autocomplete_fields = ['visitor']
    extra = 0


class ReservationAdmin(ModelAdmin):
    list_display = ['id', 'contact_email', 'contact_phone', 'confirmed_at', 'link_sent', 'groupe', 'nom_groupe']
    list_filter = ['link_sent', 'groupe', 'all_mails_required']
    search_fields = ['contact_email', 'contact_phone', 'nom_groupe']
    readonly_fields = ['created_at', 'updated_at', 'confirmed_at', 'link_token', 'link_valid_from']
    inlines = [SejoursInline]
    conditional_fields = {
        'nom_groupe': 'groupe == true',
        'groupe_profile': 'groupe == true',
        'number_visitors': 'groupe == true',
    }

    def has_module_permission(self, request):
        # Masqué de l'index/sidebar, mais les vues (édition des paramètres
        # depuis le widget) restent accessibles.
        return False

    def has_view_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def get_form(self, request, obj=None, change=False, **kwargs):
        if obj is None:
            kwargs['form'] = ReservationAddForm
        return super().get_form(request, obj, change=change, **kwargs)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return [
                (None, {'fields': ['arrival_date', 'departure_date', 'remarques_accueil']}),
                ('Contact', {'fields': ['contact_email', 'contact_phone']}),
                ('Groupe', {'fields': ['groupe', 'nom_groupe', 'groupe_profile', 'number_visitors']}),
            ]
        return super().get_fieldsets(request, obj)

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields if obj else []

    def save_model(self, request, obj, form, change):
        if not change:
            # Saisie par l'accueil : confirmée d'office, lien verrouillé
            # (« envoyer le lien » le rouvre au besoin).
            obj.link_token = uuid.uuid4()
            obj.authorize_edition = False
            obj.link_sent = False
            obj.all_mails_required = False
            obj.max_days_change = 2
            obj.max_visitors = 1
            obj.confirmed_at = timezone.now()
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        sejours = formset.save(commit=False)
        for sejour in sejours:
            if sejour.pk is None:
                sejour.confirmed = True
                if not change:
                    sejour.arrival_date = sejour.arrival_date or form.cleaned_data['arrival_date']
                    sejour.departure_date = sejour.departure_date or form.cleaned_data['departure_date']
            sejour.save()
        for sejour in formset.deleted_objects:
            sejour.delete()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        reservation = form.instance
        if not change and reservation.groupe:
            data = form.cleaned_data
            for i in range(1, data['number_visitors'] + 1):
                visitor = Visitors.objects.create(
                    nom=reservation.nom_groupe, prenom=f'Personne {i}', confirmed=False,
                )
                Sejours.objects.create(
                    reservation=reservation, visitor=visitor, confirmed=True,
                    arrival_date=data['arrival_date'], departure_date=data['departure_date'],
                    price=data['groupe_profile'].price,
                )
        if not change:
            reservation.max_visitors = max(1, Sejours.objects.filter(reservation=reservation).count())
            reservation.save(update_fields=['max_visitors', 'updated_at'])

    def response_add(self, request, obj, post_url_continue=None):
        if '_addanother' in request.POST or '_continue' in request.POST:
            return super().response_add(request, obj, post_url_continue)
        messages.success(request, f"Réservation {obj.id} créée.")
        return redirect(reverse('viale_manager:viale_manager_sejours_changelist'))



viale_admin.register(Sejours, SejourAdmin)
viale_admin.register(Reservations, ReservationAdmin)