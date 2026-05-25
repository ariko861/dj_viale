from datetime import date, timedelta

from django import forms

from unfold.contrib.forms.widgets import WysiwygWidget

from core.models import DocumentReunion, Membre, ModeleDocument, Reunion


class DocumentAutreReunionField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        date_reunion = obj.reunion.debut.strftime('%d/%m/%Y')
        nom = obj.nom or obj.fichier.name.split('/')[-1]
        return f'{obj.reunion.organe} - {date_reunion} — {nom}'


class MembreChoiceField(forms.TypedChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('coerce', int)
        kwargs.setdefault('empty_value', 0)
        kwargs['choices'] = self._get_choices
        super().__init__(*args, **kwargs)

    @staticmethod
    def _get_choices():
        return [(0, '—')] + [
            (m.pk, str(m))
            for m in Membre.objects.order_by('nom', 'prenom')
        ]


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
    documents_autres_reunions = DocumentAutreReunionField(
        label="Documents d'autres réunions joints",
        queryset=DocumentReunion.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Documents des réunions sur les 2 dernières années.',
    )

    def __init__(self, *args, reunion=None, **kwargs):
        super().__init__(*args, **kwargs)
        if reunion:
            limite = date.today() - timedelta(days=730)
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
            self.fields['documents_autres_reunions'].queryset = (
                DocumentReunion.objects
                .filter(reunion__debut__date__gte=limite)
                .exclude(reunion=reunion)
                .exclude(fichier='')
                .select_related('reunion')
                .order_by('-reunion__debut', 'nom')
            )