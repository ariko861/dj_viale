"""Comptes visiteurs, sur le parcours de réinitialisation de mot de passe de Django.

Seules changent la sélection des comptes (emails de visiteurs, cf.
:class:`~viale_manager.forms.InscriptionForm`) et la confirmation, qui active
le compte et le lie à une fiche (cf. :class:`~viale_manager.forms.ActivationForm`).
"""
from datetime import date

from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy

from viale_manager.forms import ActivationForm, ConnexionForm, InscriptionForm
from viale_manager.models import Sejours


class InscriptionView(auth_views.PasswordResetView):
    form_class = InscriptionForm
    template_name = 'viale_manager/compte/inscription.html'
    subject_template_name = 'viale_manager/mail/compte_lien_sujet.txt'
    email_template_name = 'viale_manager/mail/compte_lien.txt'
    html_email_template_name = 'viale_manager/mail/compte_lien.html'
    success_url = reverse_lazy('compte_inscription_envoyee')


class InscriptionEnvoyeeView(auth_views.PasswordResetDoneView):
    template_name = 'viale_manager/compte/inscription_envoyee.html'


class ActivationView(auth_views.PasswordResetConfirmView):
    form_class = ActivationForm
    template_name = 'viale_manager/compte/activer.html'
    post_reset_login = True
    post_reset_login_backend = 'django.contrib.auth.backends.ModelBackend'
    success_url = reverse_lazy('compte')


class ConnexionView(auth_views.LoginView):
    template_name = 'viale_manager/compte/connexion.html'
    authentication_form = ConnexionForm
    next_page = reverse_lazy('compte')


@login_required(login_url=reverse_lazy('compte_connexion'))
def mon_compte(request):
    visitor = getattr(request.user, 'visiteur', None)
    sejours = (
        Sejours.objects.filter(visitor=visitor).order_by('-arrival_date')
        if visitor else Sejours.objects.none()
    )
    today = date.today()
    return render(request, 'viale_manager/compte/mon_compte.html', {
        'visitor': visitor,
        'a_venir': [s for s in sejours if s.departure_date is None or s.departure_date >= today],
        'passes': [s for s in sejours if s.departure_date is not None and s.departure_date < today],
    })
