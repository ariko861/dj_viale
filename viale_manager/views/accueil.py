from constance import config
from django.shortcuts import render


def accueil(request):
    """Page d'accueil publique : coordonnées de la Viale, accès discret aux comptes."""
    return render(request, 'viale_manager/accueil.html', {
        'email': config.VIALE_EMAIL,
        'telephone': config.VIALE_TELEPHONE,
        'adresse': config.VIALE_ADRESSE,
    })
