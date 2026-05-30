from django import forms
from unfold.widgets import (
    UnfoldAdminEmailInputWidget,
    UnfoldAdminIntegerFieldWidget,
    UnfoldAdminTextareaWidget,
    UnfoldBooleanSwitchWidget,
)

from viale_manager.models import Reservations


class ReservationLinkForm(forms.ModelForm):
    """Formulaire de création d'un lien de réservation (modal admin)."""

    class Meta:
        model = Reservations
        fields = [
            'max_days_change', 'max_visitors', 'contact_email',
            'all_mails_required', 'groupe', 'remarques_accueil',
        ]
        widgets = {
            'max_days_change': UnfoldAdminIntegerFieldWidget(attrs={'min': 0}),
            'max_visitors': UnfoldAdminIntegerFieldWidget(attrs={'min': 1}),
            'contact_email': UnfoldAdminEmailInputWidget(),
            'all_mails_required': UnfoldBooleanSwitchWidget(),
            'groupe': UnfoldBooleanSwitchWidget(),
            'remarques_accueil': UnfoldAdminTextareaWidget(attrs={'rows': 4}),
        }
        labels = {
            'max_days_change': 'Nombre de jours de décalage possibles',
            'max_visitors': 'Nombre de visiteurs maximum',
            'contact_email': 'Email de la personne de contact',
            'all_mails_required': 'Exiger les emails de tous les inscrits',
            'groupe': 'Formulaire pour grand groupe',
            'remarques_accueil': 'Remarques accueil',
        }
        help_texts = {
            'groupe': "Formulaire spécial pour grands groupes, simplifié : seuls "
                      "les noms et prénoms seront demandés (dates et prix individuels "
                      "ne pourront pas être définis).",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['max_days_change'].required = True
        self.fields['max_visitors'].required = True