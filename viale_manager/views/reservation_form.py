import json
from datetime import date, datetime

from django.contrib.auth.models import PermissionsMixin
from django.db import transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from viale_manager.mailing import send_confirmation_auto_mails
from viale_manager.models import Messages, Profiles, Reservations, Sejours, Visitors


def _parse_date(value):
    """Parse une date 'YYYY-MM-DD' ; renvoie None si vide/invalide."""
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


class ReservationFormView(View):
    """Formulaire public (wizard) accessible via le token de la réservation."""

    def get_reservation(self, token):
        return get_object_or_404(Reservations, link_token=token)

    def get(self, request, token):
        reservation = self.get_reservation(token)
        profiles = list(Profiles.objects.all().order_by('-is_default', 'name'))
        sejours = (
            Sejours.objects
            .filter(reservation=reservation)
            .select_related('visitor')
            .order_by('arrival_date', 'id')
        )

        # Pré-remplissage si la réservation a déjà des séjours (ré-édition).
        sejours_initiaux = [
            {
                'visitorId': s.visitor_id,
                'nom': s.visitor.nom,
                'prenom': s.visitor.prenom,
                'email': s.visitor.email or '',
                'phone': s.visitor.phone or '',
                'dob': s.visitor.date_de_naissance.isoformat() if s.visitor.date_de_naissance else '',
                'price': s.price,
                'arrival': s.arrival_date.isoformat() if s.arrival_date else '',
                'departure': s.departure_date.isoformat() if s.departure_date else '',
            }
            for s in sejours
        ]
        dates = [s.arrival_date for s in sejours if s.arrival_date]
        departs = [s.departure_date for s in sejours if s.departure_date]

        messages = Messages.objects.order_by('id')

        context = {
            'reservation': reservation,
            'is_groupe': reservation.groupe,
            'messages_link': messages.filter(type=Messages.TypeMessage.LINK),
            'messages_confirmation': messages.filter(type=Messages.TypeMessage.CONFIRMATION),
            'readonly': bool(reservation.confirmed_at) and not reservation.authorize_edition,
            'profiles': [
                {'id': p.id, 'name': p.name, 'price': p.price, 'is_default': p.is_default}
                for p in profiles
            ],
            'sejours_initiaux': sejours_initiaux,
            'arrival_initial': min(dates).isoformat() if dates else '',
            'departure_initial': max(departs).isoformat() if departs else '',
            'max_visitors': reservation.max_visitors,
            'max_days_change': reservation.max_days_change,
            'all_mails_required': reservation.all_mails_required,
            'contact_email_initial': reservation.contact_email or '',
            'contact_phone_initial': reservation.contact_phone or '',
            'remarques_initial': reservation.remarques_visiteur or '',
        }
        return render(request, 'viale_manager/reservation_form.html', context)

    def post(self, request, token):
        reservation = self.get_reservation(token)
        if reservation.confirmed_at and not reservation.authorize_edition:
            return JsonResponse(
                {'ok': False, 'errors': {'__all__': "Cette réservation ne peut plus être modifiée."}},
                status=403,
            )

        try:
            payload = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'ok': False, 'errors': {'__all__': "Données invalides."}}, status=400)

        errors = {}

        arrival = _parse_date(payload.get('arrival'))
        departure = _parse_date(payload.get('departure'))
        if not arrival or not departure:
            errors['dates'] = "Les dates d'arrivée et de départ sont obligatoires."
        elif departure <= arrival:
            errors['dates'] = "La date de départ doit être après la date d'arrivée."

        raw_sejours = payload.get('sejours') or []
        if not raw_sejours:
            errors['sejours'] = "Ajoutez au moins un séjour."
        elif len(raw_sejours) > reservation.max_visitors:
            errors['sejours'] = f"Maximum {reservation.max_visitors} séjour(s) autorisé(s)."

        # En mode groupe, le formulaire est simplifié : nom/prénom (et email si
        # exigé) par visiteur ; tous les séjours partagent les dates principales
        # et un unique profil de prix choisi pour tout le groupe.
        is_groupe = reservation.groupe
        group_profile = None
        if is_groupe:
            group_profile = Profiles.objects.filter(id=payload.get('groupProfileId')).first()
            if group_profile is None:
                errors['profile'] = "Choisissez un profil de prix pour le groupe."

        max_delta = reservation.max_days_change
        cleaned = []
        for i, s in enumerate(raw_sejours):
            ligne = {}
            visitor_id = s.get('visitorId')
            nom = (s.get('nom') or '').strip()
            prenom = (s.get('prenom') or '').strip()
            email = (s.get('email') or '').strip()

            if not visitor_id and (not nom or not prenom):
                ligne['visitor'] = "Nom et prénom obligatoires."
            if reservation.all_mails_required and not email:
                ligne['email'] = "Email obligatoire."

            if is_groupe:
                phone = ''
                dob = None
                profile = group_profile
                s_arrival, s_departure = arrival, departure
            else:
                phone = (s.get('phone') or '').strip()
                dob = _parse_date(s.get('dob'))
                profile = Profiles.objects.filter(id=s.get('profileId')).first()
                if profile is None:
                    ligne['profile'] = "Choisissez un profil de prix."

                s_arrival = _parse_date(s.get('arrival')) or arrival
                s_departure = _parse_date(s.get('departure')) or departure
                if s_arrival and s_departure and s_departure <= s_arrival:
                    ligne['dates'] = "La date de départ doit être après la date d'arrivée."
                elif arrival and departure and max_delta is not None:
                    if abs((s_arrival - arrival).days) > max_delta or abs((s_departure - departure).days) > max_delta:
                        ligne['dates'] = f"Les dates ne peuvent pas varier de plus de {max_delta} jour(s)."

            if ligne:
                errors[f'sejour_{i}'] = ligne
            cleaned.append({
                'visitor_id': visitor_id, 'nom': nom, 'prenom': prenom,
                'email': email, 'phone': phone, 'dob': dob, 'profile': profile,
                'arrival': s_arrival, 'departure': s_departure,
            })

        if errors:
            return JsonResponse({'ok': False, 'errors': errors}, status=400)

        contact_email = (payload.get('contactEmail') or '').strip()
        if not contact_email and cleaned:
            contact_email = cleaned[0]['email']
        contact_phone = (payload.get('contactPhone') or '').strip()
        if not contact_phone and cleaned:
            contact_phone = cleaned[0]['phone']
        remarques = (payload.get('remarques') or '').strip()

        was_confirmed = bool(reservation.confirmed_at)
        now = timezone.now()
        with transaction.atomic():
            # Ré-soumission : on repart des séjours soumis.
            Sejours.objects.filter(reservation=reservation).delete()

            for c in cleaned:
                if c['visitor_id']:
                    visitor = Visitors.objects.filter(id=c['visitor_id']).first()
                    if visitor is None:
                        visitor = self._creer_visitor(c, now)
                else:
                    visitor = self._creer_visitor(c, now)

                Sejours.objects.create(
                    reservation=reservation,
                    visitor=visitor,
                    arrival_date=c['arrival'],
                    departure_date=c['departure'],
                    price=c['profile'].price if c['profile'] else None,
                    confirmed=False,
                    remove_from_stats=False,
                )

            reservation.contact_email = contact_email
            reservation.contact_phone = contact_phone
            reservation.remarques_visiteur = remarques
            reservation.confirmed_at = now
            reservation.updated_at = now
            reservation.save(update_fields=[
                'contact_email', 'contact_phone', 'remarques_visiteur', 'confirmed_at', 'updated_at',
            ])

        # Emails automatiques « confirmation » : uniquement à la première confirmation.
        if not was_confirmed:
            recipients = {contact_email} | {c['email'] for c in cleaned}
            send_confirmation_auto_mails(sorted(e for e in recipients if e))

        return JsonResponse({'ok': True})

    @staticmethod
    def _creer_visitor(c, now):
        return Visitors.objects.create(
            nom=c['nom'], prenom=c['prenom'],
            email=c['email'] or None, phone=c['phone'] or None,
            date_de_naissance=c['dob'],
            confirmed=False, created_at=now, updated_at=now,
        )


def visitor_search(request, token):
    """Recherche JSON de visiteurs par email (pour l'autocomplete du wizard).

    Confidentialité : un utilisateur public ne peut retrouver un visiteur que par
    correspondance EXACTE de l'email (sinon on divulguerait les coordonnées
    d'autres visiteurs). Le staff connecté garde la recherche partielle.
    """
    get_object_or_404(Reservations, link_token=token)
    q = (request.GET.get('q') or '').strip()
    if len(q) < 3:
        return JsonResponse([], safe=False)

    if request.user.is_authenticated and request.user.has_perm('viale_manager.view_visitor'):
        lookup = Q(email__icontains=q)
    else:
        lookup = Q(email__iexact=q)

    visitors = (
        Visitors.objects
        .filter(lookup)
        .exclude(email__isnull=True)
        .order_by('email')[:8]
    )
    data = [
        {
            'id': v.id, 'nom': v.nom, 'prenom': v.prenom,
            'email': v.email, 'phone': v.phone or '',
            'dob': v.date_de_naissance.isoformat() if v.date_de_naissance else '',
        }
        for v in visitors
    ]
    return JsonResponse(data, safe=False)