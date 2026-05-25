from django import forms

from unfold.contrib.forms.widgets import WysiwygWidget

from core.models import DocumentReunion, Membre, ModeleDocument


class EnvoyerEmailForm(forms.Form):
    destinataires = forms.ModelMultipleChoiceField(
        label='Destinataires',
        queryset=Membre.objects.none(),
        widget=forms.CheckboxSelectMultiple,
    )
    sujet = forms.CharField(label='Sujet', max_length=255)
    reply_to = forms.EmailField(
        label='Répondre à (reply-to)',
        required=False,
        help_text='Laisser vide pour ne pas définir de reply-to.',
    )
    corps = forms.CharField(label='Message', widget=WysiwygWidget)
    joindre_ical = forms.BooleanField(
        label="Joindre l'invitation calendrier (iCal)",
        required=False,
        initial=True,
    )
    documents = forms.ModelMultipleChoiceField(
        label='Modèles de documents joints',
        queryset=ModeleDocument.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    documents_reunion = forms.ModelMultipleChoiceField(
        label='Documents de la réunion joints',
        queryset=DocumentReunion.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, reunion=None, **kwargs):
        super().__init__(*args, **kwargs)
        if reunion:
            self.fields['destinataires'].queryset = (
                Membre.objects.filter(membrereunion__reunion=reunion)
                .order_by('nom', 'prenom')
            )
            self.fields['documents'].queryset = (
                ModeleDocument.objects.filter(organes=reunion.organe, disponible_par_mail=True)
                .select_related('tag')
            )
            self.fields['documents_reunion'].queryset = (
                DocumentReunion.objects.filter(reunion=reunion)
            )