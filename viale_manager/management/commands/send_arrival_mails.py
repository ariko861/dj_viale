from datetime import date, timedelta

from django.core.management.base import BaseCommand

from viale_manager.mailing import send_auto_mail
from viale_manager.models import AutoMails, Sejours


class Command(BaseCommand):
    help = (
        "Envoie les emails automatiques « arrivée » actifs aux visiteurs dont un "
        "séjour confirmé commence à aujourd'hui − time_delta. À lancer une fois par jour."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Affiche les destinataires sans envoyer.",
        )

    def handle(self, *args, dry_run=False, **options):
        mails = AutoMails.objects.filter(type=AutoMails.TypeAutoMail.ARRIVAL, actif=True)
        for mail in mails:
            # time_delta négatif = avant l'arrivée : -5 vise les arrivées dans 5 jours.
            arrival = date.today() - timedelta(days=mail.time_delta or 0)
            sejours = (
                Sejours.objects
                .filter(arrival_date=arrival, confirmed=True)
                .select_related('visitor', 'reservation')
            )
            # Les visiteurs d'un groupe n'ont pas d'email : on inclut le contact.
            recipients = sorted(
                {s.visitor.email for s in sejours if s.visitor.email}
                | {s.reservation.contact_email for s in sejours if s.reservation.contact_email}
            )

            if not dry_run:
                send_auto_mail(mail, recipients)
            verb = 'serait envoyé' if dry_run else 'envoyé'
            self.stdout.write(
                f"« {mail.sujet} » (arrivées du {arrival:%d/%m/%Y}) {verb} à {len(recipients)} personne(s)"
            )
            if dry_run:
                for email in recipients:
                    self.stdout.write(f"  {email}")
