import uuid

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from viale_manager.models import Reservations, Sejours


def _back(request):
    return redirect(request.META.get('HTTP_REFERER') or 'viale_manager:index')


@require_POST
def reservation_create_link(request):
    """Crée une nouvelle réservation vide avec un token, prête à être partagée."""
    now = timezone.now()
    Reservations.objects.create(
        link_token=uuid.uuid4(),
        authorize_edition=True,
        max_days_change=2,
        max_visitors=10,
        link_sent=False,
        all_mails_required=False,
        groupe=False,
        created_at=now,
        updated_at=now,
    )
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