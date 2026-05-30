import uuid

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from viale_manager.forms import ReservationLinkForm
from viale_manager.models import Reservations, Sejours


def _back(request):
    return redirect(request.META.get('HTTP_REFERER') or 'viale_manager:index')


@require_POST
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
    reservation.updated_at = now
    reservation.save()
    messages.success(request, "Lien de réservation créé.")
    return _back(request)


@require_POST
def reservation_toggle_link_sent(request, pk):
    reservation = get_object_or_404(Reservations, pk=pk)
    reservation.link_sent = not reservation.link_sent
    reservation.updated_at = timezone.now()
    reservation.save(update_fields=['link_sent', 'updated_at'])
    return _back(request)


@require_POST
def reservation_delete(request, pk):
    reservation = get_object_or_404(Reservations, pk=pk)
    with transaction.atomic():
        Sejours.objects.filter(reservation=reservation).delete()
        reservation.delete()
    messages.success(request, "Réservation supprimée.")
    return _back(request)