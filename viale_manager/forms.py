from django import forms
from unfold.widgets import (
    UnfoldAdminEmailInputWidget,
    UnfoldAdminIntegerFieldWidget,
    UnfoldAdminTextareaWidget,
    UnfoldAdminSelectWidget,
    UnfoldAdminSingleDateWidget,
    UnfoldAdminTextInputWidget,
    UnfoldBooleanSwitchWidget,
)

from viale_manager.models import Profiles, Reservations, Sejours


class ReservationLinkForm(forms.ModelForm):
    """Formulaire de création d'un lien de réservation (modal admin)."""

    class Meta:
        model = Reservations
        fields = [
            'max_days_change', 'max_visitors', 'contact_email',
            'all_mails_required', 'groupe', 'nom_groupe', 'remarques_accueil',
        ]
        widgets = {
            'max_days_change': UnfoldAdminIntegerFieldWidget(attrs={'min': 0}),
            'max_visitors': UnfoldAdminIntegerFieldWidget(attrs={'min': 1}),
            'contact_email': UnfoldAdminEmailInputWidget(),
            'all_mails_required': UnfoldBooleanSwitchWidget(),
            'groupe': UnfoldBooleanSwitchWidget(attrs={'x-model': 'groupe'}),
            'nom_groupe': UnfoldAdminTextInputWidget(),
            'remarques_accueil': UnfoldAdminTextareaWidget(attrs={'rows': 4}),
        }
        labels = {
            'max_days_change': 'Nombre de jours de décalage possibles',
            'max_visitors': 'Nombre de visiteurs maximum',
            'contact_email': 'Email de la personne de contact',
            'all_mails_required': 'Exiger les emails de tous les inscrits',
            'groupe': 'Formulaire pour grand groupe',
            'nom_groupe': 'Nom du groupe',
            'remarques_accueil': 'Remarques accueil',
        }
        help_texts = {
            'groupe': "Formulaire spécial pour grands groupes, simplifié : seuls "
                      "les prénoms seront demandés, le nom du groupe servant de nom "
                      "de famille (dates et prix individuels ne pourront pas être définis).",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['max_days_change'].required = True
        self.fields['max_visitors'].required = True

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('groupe'):
            # Le formulaire groupe ne demande pas d'email par personne.
            cleaned['all_mails_required'] = False
            if not cleaned.get('nom_groupe'):
                self.add_error('nom_groupe', "Obligatoire pour un groupe.")
            if not cleaned.get('contact_email'):
                self.add_error('contact_email', "Obligatoire pour un groupe.")
        return cleaned


class ReservationAddForm(forms.ModelForm):
    """Création directe d'une réservation par l'accueil (page d'ajout admin).

    Les dates servent de valeur par défaut aux séjours de l'inline. En mode
    groupe, l'inline reste vide : ``number_visitors`` séjours sont créés au nom
    du groupe.
    """

    arrival_date = forms.DateField(label="Date d'arrivée", widget=UnfoldAdminSingleDateWidget)
    departure_date = forms.DateField(
        label='Date de départ', required=False, widget=UnfoldAdminSingleDateWidget,
        help_text="Laisser vide si la date de départ n'est pas connue.",
    )
    groupe_profile = forms.ModelChoiceField(
        Profiles.objects.order_by('-is_default', 'name'), label='Profil de prix du groupe',
        required=False, widget=UnfoldAdminSelectWidget,
    )
    number_visitors = forms.IntegerField(
        label='Nombre de visiteurs', min_value=1, required=False,
        widget=UnfoldAdminIntegerFieldWidget(attrs={'min': 1}),
    )

    class Meta:
        model = Reservations
        fields = ['groupe', 'nom_groupe', 'contact_email', 'contact_phone', 'remarques_accueil']
        labels = {
            'groupe': 'Groupe',
            'nom_groupe': 'Nom du groupe',
            'contact_email': 'Email de contact',
            'contact_phone': 'Téléphone de contact',
            'remarques_accueil': 'Remarques accueil',
        }
        help_texts = {
            'groupe': "Crée N visiteurs « Personne i » au nom du groupe, aux mêmes dates et au même prix.",
        }

    def clean(self):
        cleaned = super().clean()
        arrival, departure = cleaned.get('arrival_date'), cleaned.get('departure_date')
        if arrival and departure and departure <= arrival:
            self.add_error('departure_date', "La date de départ doit être après la date d'arrivée.")
        if cleaned.get('groupe'):
            for name in ('nom_groupe', 'contact_email', 'groupe_profile', 'number_visitors'):
                if not cleaned.get(name):
                    self.add_error(name, "Obligatoire pour un groupe.")
        return cleaned


class SejourInlineForm(forms.ModelForm):
    """Séjour saisi dans l'inline de la réservation.

    Le profil de prix, s'il est choisi, fixe le prix. À la création, les dates
    vides reprennent celles de la réservation.
    """

    profile = forms.ModelChoiceField(
        Profiles.objects.order_by('-is_default', 'name'), label='Profil de prix',
        required=False, widget=UnfoldAdminSelectWidget,
    )

    class Meta:
        model = Sejours
        fields = ['visitor', 'profile', 'price', 'arrival_date', 'departure_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['arrival_date'].required = False

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('profile'):
            cleaned['price'] = cleaned['profile'].price
        arrival, departure = cleaned.get('arrival_date'), cleaned.get('departure_date')
        if arrival and departure and departure <= arrival:
            self.add_error('departure_date', "La date de départ doit être après la date d'arrivée.")
        return cleaned


class SejourInlineFormSet(forms.BaseInlineFormSet):

    def clean(self):
        super().clean()
        rows = [
            f for f in self.forms
            if f.has_changed() and not self._should_delete_form(f) and f.cleaned_data
        ]
        if self.instance.pk is None:
            if self.instance.groupe and rows:
                raise forms.ValidationError(
                    "Pour un groupe, n'ajoutez pas de personnes : indiquez le nombre de visiteurs."
                )
            if not self.instance.groupe and not rows:
                raise forms.ValidationError("Ajoutez au moins une personne.")
        else:
            # En modification, il n'y a pas de dates de réservation par défaut.
            for f in rows:
                if not f.cleaned_data.get('arrival_date'):
                    f.add_error('arrival_date', "Obligatoire.")
