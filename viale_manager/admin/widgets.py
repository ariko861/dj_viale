from django.urls import reverse

from viale_manager.models import Reservations


def reservations_widget_context(request, limit=8):
    """Contexte du widget de gestion des liens de réservation.

    Réutilisé dans l'index admin et au-dessus de la liste des séjours.
    """
    reservations = []
    for r in Reservations.objects.order_by('-id')[:limit]:
        reservations.append({
            'id': r.id,
            'public_url': request.build_absolute_uri(
                reverse('reservation_form', args=[r.link_token])
            ),
            'edit_url': reverse('viale_manager:viale_manager_reservations_change', args=[r.id]),
            'toggle_url': reverse('viale_manager:viale_manager_reservation_toggle_link_sent', args=[r.id]),
            'delete_url': reverse('viale_manager:viale_manager_reservation_delete', args=[r.id]),
            'link_sent': r.link_sent,
            'confirmed': bool(r.confirmed_at),
            'groupe': r.groupe,
            'remarques_accueil': r.remarques_accueil or '',
        })

    return {
        'reservation_widget': {
            'reservations': reservations,
            'create_url': reverse('viale_manager:viale_manager_reservation_create_link'),
        }
    }