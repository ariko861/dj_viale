from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.db import transaction
from unfold.forms import BaseDialogForm
from unfold.widgets import (
    UnfoldAdminEmailInputWidget,
    UnfoldAdminIntegerFieldWidget,
    UnfoldAdminTextareaWidget,
    UnfoldAdminSelectWidget,
    UnfoldAdminSingleDateWidget,
    UnfoldAdminTextInputWidget,
    UnfoldBooleanSwitchWidget,
)

from viale_manager.models import Profiles, Reservations, Sejours, Visitors


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


class NativeDateWidget(UnfoldAdminTextInputWidget):
    """Sélecteur de date natif : le calendrier admin ne s'initialise pas dans les dialogs."""

    input_type = 'date'


class SejourDatesDialogForm(BaseDialogForm):
    arrival_date = forms.DateField(label="Date d'arrivée", widget=NativeDateWidget)
    departure_date = forms.DateField(
        label='Date de départ', required=False, widget=NativeDateWidget,
        help_text="Laisser vide si la date de départ n'est pas connue.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sejour = Sejours.objects.get(pk=self.object_id)
        self.fields['arrival_date'].initial = self.sejour.arrival_date
        self.fields['departure_date'].initial = self.sejour.departure_date

    def clean(self):
        cleaned = super().clean()
        arrival, departure = cleaned.get('arrival_date'), cleaned.get('departure_date')
        if arrival and departure and departure <= arrival:
            self.add_error('departure_date', "La date de départ doit être après la date d'arrivée.")
        return cleaned


class SejourBreakDialogForm(BaseDialogForm):
    begin = forms.DateField(label="Début de l'absence", widget=NativeDateWidget)
    end = forms.DateField(label='Retour', widget=NativeDateWidget)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sejour = Sejours.objects.get(pk=self.object_id)

    def clean(self):
        cleaned = super().clean()
        begin, end = cleaned.get('begin'), cleaned.get('end')
        if not begin or not end:
            return cleaned
        s = self.sejour
        if begin <= s.arrival_date:
            self.add_error('begin', "L'absence doit commencer après l'arrivée.")
        if end <= begin:
            self.add_error('end', "Le retour doit être après le début de l'absence.")
        elif s.departure_date and end >= s.departure_date:
            self.add_error('end', "Le retour doit être avant la date de départ.")
        return cleaned


class InscriptionForm(PasswordResetForm):
    """Demande de lien : création de compte ou nouveau mot de passe.

    Reprend l'envoi de :class:`~django.contrib.auth.forms.PasswordResetForm` ;
    seule change la sélection des comptes. Pour l'email d'un visiteur sans
    compte, un compte inactif sans mot de passe est créé : il ne s'active
    qu'au clic sur le lien, avec le mot de passe choisi à ce moment-là.
    """

    def get_users(self, email):
        User = get_user_model()
        email = email.strip().lower()
        user = User.objects.filter(username=email).first()
        if user is None:
            if not Visitors.par_email(email).exists():
                return []
            user = User(username=email, email=email, is_active=False)
            user.set_unusable_password()
            user.save()
            return [user]
        if user.is_active:
            return [user]
        # Inactif avec un mot de passe : compte désactivé par l'accueil, pas une inscription en cours.
        if user.has_usable_password():
            return []
        return [user] if Visitors.par_email(email).exists() else []


class ActivationForm(SetPasswordForm):
    """Mot de passe (formulaire Django) et, pour un nouveau compte, choix de la fiche."""

    visitor = forms.ModelChoiceField(
        queryset=Visitors.objects.none(), widget=forms.RadioSelect, empty_label=None,
        label='Quelle fiche est la vôtre ?',
    )
    field_order = ['visitor', 'new_password1', 'new_password2']
    plus_de_fiche = False

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields['new_password1'].label = 'Mot de passe'
        self.fields['new_password2'].label = 'Confirmation'
        if Visitors.objects.filter(user=user).exists():
            del self.fields['visitor']
            return
        fiches = Visitors.par_email(user.email).order_by('nom', 'prenom')
        self.fields['visitor'].queryset = fiches
        # Fiche prise entre-temps par un autre compte : plus rien à lier.
        self.plus_de_fiche = not fiches.exists()
        if fiches.count() == 1:
            self.fields['visitor'].initial = fiches.first()
            self.fields['visitor'].widget = forms.HiddenInput()

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = True
        user.save()
        visitor = self.cleaned_data.get('visitor')
        if visitor:
            visitor.user = user
            visitor.save(update_fields=['user', 'updated_at'])
        return user


class ConnexionForm(AuthenticationForm):
    """Connexion par email (l'email, en minuscules, sert de nom d'utilisateur)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'

    def clean_username(self):
        return self.cleaned_data['username'].strip().lower()


class EnvoiEmailForm(forms.Form):
    """Email libre aux visiteurs sélectionnés (action de l'admin)."""

    sujet = forms.CharField(label='Sujet', max_length=200, widget=UnfoldAdminTextInputWidget)
    message = forms.CharField(
        label='Message', widget=UnfoldAdminTextareaWidget(attrs={'rows': 10}),
        help_text="Texte simple ; les retours à la ligne sont conservés.",
    )
