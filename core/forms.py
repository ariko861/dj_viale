from django import forms

from core.models import Membre, ModeleDocument


class EnvoyerEmailForm(forms.Form):
    destinataires = forms.ModelMultipleChoiceField(
        label='Destinataires',
        queryset=Membre.objects.none(),
        widget=forms.CheckboxSelectMultiple,
    )
    sujet = forms.CharField(label='Sujet', max_length=255)
    corps = forms.CharField(label='Message', widget=forms.Textarea(attrs={'rows': 12}))
    documents = forms.ModelMultipleChoiceField(
        label='Documents joints',
        queryset=ModeleDocument.objects.none(),
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
                ModeleDocument.objects.filter(organes=reunion.organe)
                .select_related('tag')
            )