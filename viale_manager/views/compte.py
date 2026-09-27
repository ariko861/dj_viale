"""Comptes visiteurs : création réservée aux emails connus, vérifiée par un lien envoyé par email."""
from datetime import date

from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core import signing
from django.utils.crypto import constant_time_compare, salted_hmac
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

from viale_manager.forms import ActivationForm, ConnexionForm, InscriptionForm
from viale_manager.mailing import send_compte_link
from viale_manager.models import Sejours, Visitors

SALT = 'viale-compte'
VALIDITE = 3 * 24 * 3600  # secondes


def _compte_existant(email):
    return get_user_model().objects.filter(username=email, is_active=True).first()


def _empreinte(user):
    """Change dès que le compte est créé ou son mot de passe modifié : le lien est à usage unique."""
    return salted_hmac(SALT, user.password if user else '').hexdigest()[:16]


def inscription(request):
    """Demande de lien. La réponse est la même que l'email soit connu ou non."""
    form = InscriptionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        user = _compte_existant(email)
        if user or Visitors.par_email(email).exists():
            token = signing.dumps({'email': email, 'h': _empreinte(user)}, salt=SALT)
            url = request.build_absolute_uri(reverse('compte_activer', args=[token]))
            send_compte_link(email, url, existe=user is not None)
        return render(request, 'viale_manager/compte/inscription_envoyee.html', {'email': email})
    return render(request, 'viale_manager/compte/inscription.html', {'form': form})


def activer(request, token):
    """Lien reçu par email : choix de la fiche et du mot de passe (ou nouveau mot de passe)."""
    try:
        payload = signing.loads(token, salt=SALT, max_age=VALIDITE)
    except signing.BadSignature:
        return render(request, 'viale_manager/compte/lien_invalide.html', status=400)
    email = payload['email']
    user = _compte_existant(email)
    if not constant_time_compare(payload.get('h', ''), _empreinte(user)):
        return render(request, 'viale_manager/compte/lien_invalide.html', status=400)
    fiches = None if user else Visitors.par_email(email).order_by('nom', 'prenom')
    if fiches is not None and not fiches.exists():
        return render(request, 'viale_manager/compte/lien_invalide.html', status=400)

    form = ActivationForm(request.POST or None, fiches=fiches)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            if user is None:
                user = get_user_model().objects.create_user(username=email, email=email)
                visitor = form.cleaned_data['visitor']
                visitor.user = user
                visitor.save(update_fields=['user', 'updated_at'])
            user.set_password(form.cleaned_data['password1'])
            user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('compte')
    return render(request, 'viale_manager/compte/activer.html', {
        'form': form, 'email': email, 'existe': user is not None,
    })


class ConnexionView(LoginView):
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
