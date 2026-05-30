from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

from viale_manager.models import AutoMails


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
        for email in recipients:
            msg = EmailMultiAlternatives(
                subject=mail.sujet,
                body=strip_tags(mail.body),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            msg.attach_alternative(mail.body, 'text/html')
            msg.send(fail_silently=True)