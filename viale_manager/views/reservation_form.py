import json
from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from viale_manager.mailing import send_confirmation_auto_mails, send_reservation_confirmed
from viale_manager.models import Messages, Profiles, Reservations, Sejours, Visitors


def _parse_date(value):
    """Parse une date 'YYYY-MM-DD' ; renvoie None si vide/invalide."""
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _is_email(value):
    try:
        validate_email(value)
    except ValidationError:
        return False
    return True


class ReservationFormView(View):
    """Formulaire public (wizard) accessible via le token de la réservation.

    Tant que ``authorize_edition`` est vrai, le lien affiche le wizard. La
    soumission confirme la réservation et verrouille le lien : il affiche
    ensuite un récapitulatif, jusqu'à ce que l'accueil ré-autorise l'édition.
    """

    def get_reservation(self, token):
        return get_object_or_404(Reservations, link_token=token)

    def get(self, request, token):
        reservation = self.get_reservation(token)
        sejours = list(
            Sejours.objects
            .filter(reservation=reservation)
            .select_related('visitor')
            .order_by('arrival_date', 'id')
        )
        messages = Messages.objects.order_by('id')

        if not reservation.authorize_edition:
            return render(request, 'viale_manager/reservation_confirmed.html', {
                'reservation': reservation,
                'sejours': sejours,
                'messages_confirmation': messages.filter(type=Messages.TypeMessage.CONFIRMATION),
            })

        profiles = list(Profiles.objects.all().order_by('-is_default', 'name'))
        profile_par_prix = {}
        for p in profiles:
            profile_par_prix.setdefault(p.price, p.id)

        # Pré-remplissage si la réservation a déjà des séjours (ré-édition).
        # Le séjour ne stocke que le prix : on retrouve le profil correspondant.
        sejours_initiaux = [
            {
                'sejourId': s.id,
                'visitorId': s.visitor_id,
                'nom': s.visitor.nom,
                'prenom': s.visitor.prenom,
                'email': s.visitor.email or '',
                'phone': s.visitor.phone or '',
                'dob': s.visitor.date_de_naissance.isoformat() if s.visitor.date_de_naissance else '',
                'profileId': profile_par_prix.get(s.price),
                'arrival': s.arrival_date.isoformat() if s.arrival_date else '',
                'departure': s.departure_date.isoformat() if s.departure_date else '',
            }
            for s in sejours
        ]
        dates = [s.arrival_date for s in sejours if s.arrival_date]
        departs = [s.departure_date for s in sejours if s.departure_date]
        group_profile_id = sejours_initiaux[0]['profileId'] if reservation.groupe and sejours_initiaux else None

        context = {
            'reservation': reservation,
            'is_groupe': reservation.groupe,
            'messages_link': messages.filter(type=Messages.TypeMessage.LINK),
            'profiles': [
                {'id': p.id, 'name': p.name, 'price': p.price, 'is_default': p.is_default}
                for p in profiles
            ],
            'sejours_initiaux': sejours_initiaux,
            'group_profile_id': group_profile_id,
            'min_arrival': '' if sejours else date.today().isoformat(),
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
        if not reservation.authorize_edition:
            return JsonResponse(
                {'ok': False, 'errors': {'__all__': "Cette réservation ne peut plus être modifiée."}},
                status=403,
            )

        try:
            payload = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'ok': False, 'errors': {'__all__': "Données invalides."}}, status=400)

        existing = {
            s.id: s for s in Sejours.objects.filter(reservation=reservation).select_related('visitor')
        }
        errors = {}

        arrival = _parse_date(payload.get('arrival'))
        departure = _parse_date(payload.get('departure'))
        if not arrival or not departure:
            errors['dates'] = "Les dates d'arrivée et de départ sont obligatoires."
        elif departure <= arrival:
            errors['dates'] = "La date de départ doit être après la date d'arrivée."
        elif not existing and arrival < date.today():
            # Seulement à la première saisie : une ré-édition peut porter sur un séjour commencé.
            errors['dates'] = "La date d'arrivée ne peut pas être dans le passé."

        raw_sejours = payload.get('sejours') or []
        if not raw_sejours:
            errors['sejours'] = "Ajoutez au moins une personne."
        elif len(raw_sejours) > reservation.max_visitors:
            errors['sejours'] = f"Maximum {reservation.max_visitors} personne(s) autorisée(s)."

        contact_email = (payload.get('contactEmail') or '').strip()
        contact_phone = (payload.get('contactPhone') or '').strip()
        if not contact_email or not _is_email(contact_email):
            errors['contactEmail'] = "Un email de contact valide est obligatoire."
        if not contact_phone:
            errors['contactPhone'] = "Le téléphone de contact est obligatoire."
        remarques = (payload.get('remarques') or '').strip()

        # En mode groupe, le formulaire est simplifié : un prénom par personne,
        # le nom du groupe servant de nom de famille ; tous les séjours partagent
        # les dates principales et un unique profil de prix.
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
            sejour_id = s.get('sejourId') if s.get('sejourId') in existing else None
            prenom = (s.get('prenom') or '').strip()

            if is_groupe:
                if not prenom:
                    ligne['visitor'] = "Prénom obligatoire."
                cleaned.append({
                    'sejour_id': sejour_id, 'visitor_id': None,
                    'nom': reservation.nom_groupe or '', 'prenom': prenom,
                    'email': '', 'phone': '', 'dob': None, 'profile': group_profile,
                    'arrival': arrival, 'departure': departure,
                })
            else:
                visitor_id = s.get('visitorId')
                nom = (s.get('nom') or '').strip()
                email = (s.get('email') or '').strip()
                phone = (s.get('phone') or '').strip()
                dob = _parse_date(s.get('dob'))

                if not visitor_id and (not nom or not prenom):
                    ligne['visitor'] = "Nom et prénom obligatoires."
                if reservation.all_mails_required and not email:
                    ligne['email'] = "Email obligatoire."
                elif email and not _is_email(email):
                    ligne['email'] = "Email invalide."
                if dob is None:
                    ligne['dob'] = "Date de naissance obligatoire."
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

                cleaned.append({
                    'sejour_id': sejour_id, 'visitor_id': visitor_id,
                    'nom': nom, 'prenom': prenom,
                    'email': email, 'phone': phone, 'dob': dob, 'profile': profile,
                    'arrival': s_arrival, 'departure': s_departure,
                })

            if ligne:
                errors[f'sejour_{i}'] = ligne

        if errors:
            return JsonResponse({'ok': False, 'errors': errors}, status=400)

        was_confirmed = bool(reservation.confirmed_at)
        now = timezone.now()
        with transaction.atomic():
            kept_ids = set()
            for c in cleaned:
                sejour = existing.get(c['sejour_id'])
                visitor = self._get_visitor(c, sejour, is_groupe)

                if sejour is None:
                    sejour = Sejours(reservation=reservation, remove_from_stats=False)
                sejour.visitor = visitor
                sejour.arrival_date = c['arrival']
                sejour.departure_date = c['departure']
                sejour.price = c['profile'].price
                sejour.confirmed = True
                sejour.save()
                kept_ids.add(sejour.id)

            # Personnes retirées du formulaire lors d'une ré-édition.
            Sejours.objects.filter(reservation=reservation).exclude(id__in=kept_ids).delete()

            reservation.contact_email = contact_email
            reservation.contact_phone = contact_phone
            reservation.remarques_visiteur = remarques
            reservation.confirmed_at = now
            reservation.authorize_edition = False
            reservation.save(update_fields=[
                'contact_email', 'contact_phone', 'remarques_visiteur',
                'confirmed_at', 'authorize_edition', 'updated_at',
            ])

        send_reservation_confirmed(request, reservation)
        # Emails automatiques « confirmation » : uniquement à la première confirmation.
        if not was_confirmed:
            recipients = {contact_email} | {c['email'] for c in cleaned}
            send_confirmation_auto_mails(sorted(e for e in recipients if e))

        return JsonResponse({'ok': True})

    @staticmethod
    def _get_visitor(c, sejour, is_groupe):
        """Visiteur du séjour : existant (complété) ou nouvellement créé."""
        if is_groupe:
            # Les visiteurs d'un groupe sont propres à la réservation : on renomme.
            if sejour is not None:
                visitor = sejour.visitor
                visitor.nom, visitor.prenom = c['nom'], c['prenom']
                visitor.save(update_fields=['nom', 'prenom', 'updated_at'])
                return visitor
            return Visitors.objects.create(nom=c['nom'], prenom=c['prenom'], confirmed=False)

        visitor = Visitors.objects.filter(id=c['visitor_id']).first() if c['visitor_id'] else None
        if visitor is None:
            return Visitors.objects.create(
                nom=c['nom'], prenom=c['prenom'],
                email=c['email'] or None, phone=c['phone'] or None,
                date_de_naissance=c['dob'], confirmed=False,
            )
        if c['phone']:
            visitor.phone = c['phone']
        if c['dob']:
            visitor.date_de_naissance = c['dob']
        visitor.save(update_fields=['phone', 'date_de_naissance', 'updated_at'])
        return visitor


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
