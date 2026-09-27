from django.urls import reverse

from core.models import DocumentReunion, Reunion


def onglets_annees(request):
    """Onglets « Toutes / 2026 / 2025 / … » sur les listes de réunions et de documents."""
    return [
        _onglets(Reunion, 'core.reunion', 'admin:core_reunion_changelist'),
        _onglets(DocumentReunion, 'core.documentreunion', 'admin:core_documentreunion_changelist'),
    ]


def _onglets(model, nom_modele, url_name):
    url = reverse(url_name)
    annees = (
        model.objects.exclude(annee=None)
        .order_by('-annee').values_list('annee', flat=True).distinct()
    )
    return {
        'models': [nom_modele],
        'items': [
            {'title': 'Toutes', 'link': url, 'active': lambda request: 'annee' not in request.GET},
            *({'title': str(annee), 'link': f'{url}?annee={annee}'} for annee in annees),
        ],
    }
