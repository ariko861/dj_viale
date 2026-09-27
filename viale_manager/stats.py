"""Calculs des statistiques et des présences, séparés des vues pour être testés."""
import json
from datetime import date, timedelta

from django.db.models import Q
from django.utils.formats import date_format

from viale_manager.models import Sejours

# Palette catégorielle validée (slots 1-3), résolue en CSS pour suivre le thème.
SERIES = [
    ('Restent', 'var(--vm-series-1)'),
    ('Arrivent', 'var(--vm-series-2)'),
    ('Partent', 'var(--vm-series-3)'),
]


def chevauchent(queryset, debut, fin):
    """Séjours présents au moins un jour entre ``debut`` et ``fin`` inclus."""
    return queryset.filter(arrival_date__lte=fin).filter(
        Q(departure_date__gte=debut) | Q(departure_date__isnull=True)
    )


def nuitees_dans_periode(sejour, debut, fin, today=None):
    """Nuits du séjour tombant dans la période (nuit du jour ``d`` : arrivée <= d < départ).

    Un séjour sans date de départ est compté jusqu'à aujourd'hui.
    """
    today = today or date.today()
    depart = sejour.departure_date or today
    start = max(sejour.arrival_date, debut)
    end = min(depart, fin + timedelta(days=1))
    return max(0, (end - start).days)


def statistiques(debut, fin, today=None):
    """Séjours confirmés et comptés dans les stats ayant au moins une nuit sur la période.

    :return: ``(lignes, totaux)`` ; chaque ligne est ``(sejour, nuitees, cout)``.
    """
    sejours = chevauchent(
        Sejours.objects.filter(confirmed=True, remove_from_stats=False), debut, fin,
    ).select_related('visitor').order_by('arrival_date', 'visitor__nom')

    lignes = []
    for s in sejours:
        n = nuitees_dans_periode(s, debut, fin, today)
        # Départ le premier jour, ou séjour ouvert pas encore commencé : aucune nuit.
        if n:
            lignes.append((s, n, n * (s.price or 0)))
    totaux = {
        'sejours': len(lignes),
        'visiteurs': len({s.visitor_id for s, _, _ in lignes}),
        'nuitees': sum(n for _, n, _ in lignes),
        'revenus': sum(c for _, _, c in lignes),
    }
    return lignes, totaux


def presences(debut, fin):
    """Par jour : (jour, restent, arrivent, partent), tous séjours confondus."""
    sejours = list(chevauchent(Sejours.objects.all(), debut, fin).values_list('arrival_date', 'departure_date'))
    jours = []
    d = debut
    while d <= fin:
        restent = sum(1 for a, dep in sejours if a < d and (dep is None or dep > d))
        arrivent = sum(1 for a, _ in sejours if a == d)
        partent = sum(1 for _, dep in sejours if dep == d)
        jours.append((d, restent, arrivent, partent))
        d += timedelta(days=1)
    return jours


def presences_chart(jours):
    """Données et options du graphique empilé, au format du composant chart d'Unfold."""
    data = {
        'labels': [date_format(d, 'D d/m') for d, *_ in jours],
        'datasets': [
            # Bordure couleur de fond : un espace de 2px sépare les segments empilés.
            {'label': label, 'data': [j[i + 1] for j in jours], 'backgroundColor': color,
             'borderColor': 'var(--vm-surface)', 'borderWidth': 2}
            for i, (label, color) in enumerate(SERIES)
        ],
    }
    options = {
        'animation': False,
        'responsive': True,
        'maintainAspectRatio': False,
        'maxBarThickness': 32,
        'datasets': {'bar': {'borderRadius': 4}},
        'plugins': {
            'legend': {'display': True, 'align': 'end', 'position': 'top',
                       'labels': {'usePointStyle': True, 'boxHeight': 8, 'boxWidth': 8}},
            'tooltip': {'enabled': True, 'mode': 'index', 'intersect': False},
        },
        'scales': {
            'x': {'stacked': True, 'grid': {'display': False}},
            'y': {'stacked': True, 'beginAtZero': True, 'ticks': {'precision': 0}},
        },
    }
    return json.dumps(data), json.dumps(options)
