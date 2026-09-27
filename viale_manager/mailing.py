from constance import config
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

from viale_manager.models import AutoMails, Sejours


def send_confirmation_auto_mails(recipient_emails):
    """Envoie les emails automatiques actifs de type « confirmation ».

    Un message HTML par destinataire (pour ne pas exposer les adresses entre
    elles). N'échoue jamais bruyamment : la confirmation de réservation ne doit
    pas être bloquée par un problème d'envoi.
    """
    recipients = [e for e in (recipient_emails or []) if e]
    if not recipients:
        return

    mails = list(AutoMails.objects.filter(
        type=AutoMails.TypeAutoMail.CONFIRMATION, actif=True,
    ))
    for mail in mails:
        send_auto_mail(mail, recipients)


def send_auto_mail(mail, recipients):
    """Envoie un email automatique, un message par destinataire."""
    for email in recipients:
        msg = EmailMultiAlternatives(
            subject=mail.sujet,
            body=strip_tags(mail.body),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
            reply_to=[config.VIALE_EMAIL] if config.VIALE_EMAIL else None,
        )
        msg.attach_alternative(mail.body, 'text/html')
        msg.send(fail_silently=True)


def _send_html(subject, template, context, to, reply_to=None, fail_silently=True):
    html = render_to_string(template, context)
    msg = EmailMultiAlternatives(
        subject=f'[Viale] {subject}',
        body=strip_tags(html),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
        reply_to=[reply_to] if reply_to else None,
    )
    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=fail_silently)


def _reservation_context(request, reservation):
    return {
        'reservation': reservation,
        'sejours': (
            Sejours.objects.filter(reservation=reservation)
            .select_related('visitor').order_by('arrival_date', 'id')
        ),
        'public_url': request.build_absolute_uri(
            reverse('reservation_form', args=[reservation.link_token])
        ),
    }


def send_reservation_link(request, reservation):
    """Envoie le lien du formulaire à la personne de contact.

    Contrairement aux notifications de confirmation, lève une exception en cas
    d'échec : l'accueil doit savoir que le lien n'est pas parti.
    """
    _send_html(
        'Lien du formulaire de réservation',
        'viale_manager/mail/reservation_link.html',
        _reservation_context(request, reservation),
        to=[reservation.contact_email],
        reply_to=config.VIALE_EMAIL,
        fail_silently=False,
    )


def send_reservation_confirmed(request, reservation):
    """Notifie la Viale et la personne de contact d'une réservation confirmée."""
    context = _reservation_context(request, reservation)

    if config.VIALE_EMAIL:
        context['admin_url'] = request.build_absolute_uri(
            reverse('viale_manager:viale_manager_reservations_change', args=[reservation.id])
        )
        _send_html(
            'Réservation confirmée',
            'viale_manager/mail/reservation_confirmed_viale.html',
            context,
            to=[config.VIALE_EMAIL],
            reply_to=reservation.contact_email,
        )

    if reservation.contact_email:
        _send_html(
            'Votre réservation est confirmée',
            'viale_manager/mail/reservation_confirmed_contact.html',
            context,
            to=[reservation.contact_email],
            reply_to=config.VIALE_EMAIL,
        )


def send_compte_link(email, url, existe):
    """Lien de création de compte (ou de nouveau mot de passe si ``existe``)."""
    _send_html(
        'Votre compte',
        'viale_manager/mail/compte_lien.html',
        {'url': url, 'existe': existe},
        to=[email],
        reply_to=config.VIALE_EMAIL,
    )
