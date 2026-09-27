import uuid

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from viale_manager.forms import ReservationLinkForm
from viale_manager.mailing import send_reservation_link
from viale_manager.models import Reservations, Sejours


def _back(request):
    return redirect(request.META.get('HTTP_REFERER') or 'viale_manager:index')


@require_POST
@permission_required('viale_manager.add_reservations', raise_exception=True)
def reservation_create_link(request):
    """Crée une nouvelle réservation avec un token, prête à être partagée."""
    form = ReservationLinkForm(request.POST)
    if not form.is_valid():
        for field, errs in form.errors.items():
            label = form.fields[field].label if field in form.fields else field
            messages.error(request, f"{label} : {' '.join(errs)}")
        return _back(request)

    now = timezone.now()
    reservation = form.save(commit=False)
    reservation.link_token = uuid.uuid4()
    reservation.authorize_edition = True
    reservation.link_sent = False
    reservation.created_at = now
    reservation.link_valid_from = now
    reservation.updated_at = now
    reservation.save()
    messages.success(request, "Lien de réservation créé.")
    return _back(request)


@require_POST
@permission_required('viale_manager.change_reservations', raise_exception=True)
def reservation_toggle_link_sent(request, pk):
    reservation = get_object_or_404(Reservations, pk=pk)
    reservation.link_sent = not reservation.link_sent
    reservation.updated_at = timezone.now()
    reservation.save(update_fields=['link_sent', 'updated_at'])
    return _back(request)


@require_POST
@permission_required('viale_manager.change_reservations', raise_exception=True)
def reservation_send_link(request, pk):
    """Envoie le lien à la personne de contact et ré-autorise l'édition."""
    reservation = get_object_or_404(Reservations, pk=pk)
    if not reservation.contact_email:
        messages.error(request, "Cette réservation n'a pas d'email de contact.")
        return _back(request)
    try:
        send_reservation_link(request, reservation)
    except Exception as e:
        messages.error(request, f"Échec de l'envoi à {reservation.contact_email} : {e}")
        return _back(request)
    reservation.authorize_edition = True
    reservation.link_sent = True
    # Un envoi fait repartir la validité du lien (VIALE_LIEN_VALIDITE_JOURS).
    reservation.link_valid_from = timezone.now()
    reservation.save(update_fields=['authorize_edition', 'link_sent', 'link_valid_from', 'updated_at'])
    messages.success(request, f"Lien envoyé à {reservation.contact_email}.")
    return _back(request)


@require_POST
@permission_required('viale_manager.delete_reservations', raise_exception=True)
def reservation_delete(request, pk):
    reservation = get_object_or_404(Reservations, pk=pk)
    with transaction.atomic():
        Sejours.objects.filter(reservation=reservation).delete()
        reservation.delete()
    messages.success(request, "Réservation supprimée.")
    return _back(request)