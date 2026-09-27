import json
import uuid
from datetime import date, timedelta

from constance.test import override_config
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from core.models import User
from viale_manager.forms import ReservationLinkForm
from viale_manager.models import Profiles, Reservations, Sejours, Visitors


def _reservation(**kwargs):
    defaults = dict(
        link_token=uuid.uuid4(), authorize_edition=True, link_sent=False,
        max_days_change=2, max_visitors=5, all_mails_required=False, groupe=False,
    )
    return Reservations.objects.create(**{**defaults, **kwargs})


@override_config(VIALE_EMAIL='accueil@viale.test')
class ReservationFormTests(TestCase):

    def setUp(self):
        self.profile = Profiles.objects.create(name='Standard', price=20, is_default=True, remarques='')
        self.arrival = date.today() + timedelta(days=10)
        self.departure = self.arrival + timedelta(days=3)

    def url(self, reservation):
        return reverse('reservation_form', args=[reservation.link_token])

    def payload(self, **kwargs):
        data = {
            'arrival': self.arrival.isoformat(),
            'departure': self.departure.isoformat(),
            'contactEmail': 'contact@example.com',
            'contactPhone': '0470000000',
            'remarques': '',
            'sejours': [{
                'nom': 'Dupont', 'prenom': 'Jean', 'email': 'jean@example.com',
                'phone': '', 'dob': '1990-01-01', 'profileId': self.profile.id,
                'arrival': '', 'departure': '',
            }],
        }
        data.update(kwargs)
        return data

    def post(self, reservation, data):
        return self.client.post(self.url(reservation), json.dumps(data), content_type='application/json')

    def test_soumission_confirme_et_verrouille(self):
        r = _reservation()
        resp = self.post(r, self.payload())
        self.assertEqual(resp.status_code, 200, resp.content)

        r.refresh_from_db()
        self.assertIsNotNone(r.confirmed_at)
        self.assertFalse(r.authorize_edition)
        sejour = Sejours.objects.get(reservation=r)
        self.assertTrue(sejour.confirmed)
        self.assertEqual(sejour.price, 20)
        self.assertEqual(sejour.arrival_date, self.arrival)
        self.assertEqual(
            sorted(m.to[0] for m in mail.outbox),
            ['accueil@viale.test', 'contact@example.com'],
        )

    def test_lien_verrouille_affiche_recap_et_refuse_post(self):
        r = _reservation()
        self.post(r, self.payload())

        resp = self.client.get(self.url(r))
        self.assertTemplateUsed(resp, 'viale_manager/reservation_confirmed.html')
        self.assertContains(resp, 'Jean Dupont')
        self.assertEqual(self.post(r, self.payload()).status_code, 403)

    def test_champs_obligatoires(self):
        r = _reservation()
        data = self.payload(contactPhone='')
        data['sejours'][0]['dob'] = ''
        resp = self.post(r, data)
        self.assertEqual(resp.status_code, 400)
        errors = resp.json()['errors']
        self.assertIn('contactPhone', errors)
        self.assertIn('dob', errors['sejour_0'])

    def test_arrivee_passee_refusee_a_la_premiere_saisie(self):
        r = _reservation()
        resp = self.post(r, self.payload(arrival=(date.today() - timedelta(days=1)).isoformat()))
        self.assertEqual(resp.status_code, 400)
        self.assertIn('dates', resp.json()['errors'])

    def test_reedition_met_a_jour_sans_recreer(self):
        r = _reservation()
        data = self.payload()
        data['sejours'].append({**data['sejours'][0], 'nom': 'Martin', 'prenom': 'Anne', 'email': ''})
        self.post(r, data)
        jean, anne = Sejours.objects.filter(reservation=r).order_by('id')
        jean.remove_from_stats = True
        jean.save()

        r.authorize_edition = True
        r.save()
        new_departure = self.departure + timedelta(days=1)
        data = self.payload()
        data['sejours'][0].update(
            sejourId=jean.id, visitorId=jean.visitor_id, phone='0499', departure=new_departure.isoformat(),
        )
        resp = self.post(r, data)
        self.assertEqual(resp.status_code, 200, resp.content)

        restants = list(Sejours.objects.filter(reservation=r))
        self.assertEqual([s.id for s in restants], [jean.id])
        self.assertTrue(restants[0].remove_from_stats)
        self.assertEqual(restants[0].departure_date, new_departure)
        self.assertEqual(restants[0].visitor.phone, '0499')

    def test_groupe_prenoms_seulement(self):
        r = _reservation(groupe=True, nom_groupe='Scouts', contact_email='chef@example.com')
        data = self.payload(
            groupProfileId=self.profile.id,
            sejours=[{'prenom': 'Paul'}, {'prenom': 'Léa'}],
        )
        resp = self.post(r, data)
        self.assertEqual(resp.status_code, 200, resp.content)
        visitors = Visitors.objects.filter(sejours__reservation=r).order_by('prenom')
        self.assertEqual([(v.nom, v.prenom) for v in visitors], [('Scouts', 'Léa'), ('Scouts', 'Paul')])


class ReservationLinkFormTests(TestCase):

    def test_groupe_exige_nom_et_contact(self):
        form = ReservationLinkForm(data={
            'max_days_change': 2, 'max_visitors': 50, 'groupe': 'on', 'all_mails_required': 'on',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('nom_groupe', form.errors)
        self.assertIn('contact_email', form.errors)

        form = ReservationLinkForm(data={
            'max_days_change': 2, 'max_visitors': 50, 'groupe': 'on', 'all_mails_required': 'on',
            'nom_groupe': 'Scouts', 'contact_email': 'chef@example.com',
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data['all_mails_required'])


class SendLinkTests(TestCase):

    def test_envoi_du_lien(self):
        admin = User.objects.create_superuser(username='admin', email='a@example.com', password='x')
        self.client.force_login(admin)
        r = _reservation(authorize_edition=False, contact_email='contact@example.com')

        resp = self.client.post(reverse('viale_manager:viale_manager_reservation_send_link', args=[r.id]))
        self.assertEqual(resp.status_code, 302)
        r.refresh_from_db()
        self.assertTrue(r.link_sent)
        self.assertTrue(r.authorize_edition)
        self.assertEqual(mail.outbox[0].to, ['contact@example.com'])
        self.assertIn(str(r.link_token), mail.outbox[0].body)


class ArrivalMailsTests(TestCase):

    def test_envoi_aux_arrivees_visees(self):
        from io import StringIO

        from django.core.management import call_command

        from viale_manager.models import AutoMails

        AutoMails.objects.create(sujet='Rappel', body='<p>Bientôt</p>', type='arrival', time_delta=-5, actif=True)
        AutoMails.objects.create(sujet='Inactif', body='x', type='arrival', time_delta=-5, actif=False)
        r = _reservation(contact_email='contact@example.com')
        dans_5_jours = date.today() + timedelta(days=5)

        def sejour(email, arrival, confirmed=True):
            v = Visitors.objects.create(nom='X', prenom='Y', email=email, confirmed=False)
            Sejours.objects.create(reservation=r, visitor=v, arrival_date=arrival, confirmed=confirmed)

        sejour('vise@example.com', dans_5_jours)
        sejour(None, dans_5_jours)
        sejour('non-confirme@example.com', dans_5_jours, confirmed=False)
        sejour('autre-date@example.com', dans_5_jours + timedelta(days=1))

        call_command('send_arrival_mails', stdout=StringIO())
        self.assertEqual(
            sorted(m.to[0] for m in mail.outbox),
            ['contact@example.com', 'vise@example.com'],
        )
        self.assertTrue(all(m.subject == 'Rappel' for m in mail.outbox))
