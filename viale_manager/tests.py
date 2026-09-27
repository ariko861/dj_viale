import json
import uuid
from datetime import date, timedelta

from constance.test import override_config
from django.core import mail
from django.test import TestCase, override_settings
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


class VisitorSearchTests(TestCase):

    def test_recherche_partielle_reservee_au_staff(self):
        from django.contrib.auth.models import Permission

        r = _reservation()
        Visitors.objects.create(nom='Dupont', prenom='Jean', email='jean.dupont@example.com', confirmed=False)
        url = reverse('reservation_visitor_search', args=[r.link_token])

        self.assertEqual(self.client.get(url, {'q': 'dupont'}).json(), [])
        self.assertEqual(len(self.client.get(url, {'q': 'jean.dupont@example.com'}).json()), 1)

        staff = User.objects.create_user(username='accueil', password='x', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='view_visitors'))
        self.client.force_login(staff)
        self.assertEqual(len(self.client.get(url, {'q': 'dupont'}).json()), 1)


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class ReservationAddAdminTests(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser(username='admin', email='a@example.com', password='x'))
        self.profile = Profiles.objects.create(name='Standard', price=20, is_default=True, remarques='')
        self.url = reverse('viale_manager:viale_manager_reservations_add')
        self.arrival = date.today() + timedelta(days=3)

    def post(self, rows=(), **data):
        payload = {
            'arrival_date': self.arrival.isoformat(), 'departure_date': '',
            'remarques_accueil': '', 'contact_email': '', 'contact_phone': '',
            'nom_groupe': '', 'groupe_profile': '', 'number_visitors': '',
            'sejours_set-TOTAL_FORMS': len(rows), 'sejours_set-INITIAL_FORMS': 0,
            'sejours_set-MIN_NUM_FORMS': 0, 'sejours_set-MAX_NUM_FORMS': 1000,
        }
        for i, row in enumerate(rows):
            for k, v in row.items():
                payload[f'sejours_set-{i}-{k}'] = v
        payload.update(data)
        return self.client.post(self.url, payload)

    def test_page_ajout_s_affiche(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_personnes_reprennent_les_dates_de_la_reservation(self):
        v = Visitors.objects.create(nom='Dupont', prenom='Jean', confirmed=False)
        resp = self.post(rows=[{'visitor': v.id, 'profile': self.profile.id, 'price': '',
                                'arrival_date': '', 'departure_date': ''}])
        self.assertEqual(resp.status_code, 302, getattr(resp, 'context_data', {}).get('errors'))

        r = Reservations.objects.get()
        self.assertIsNotNone(r.confirmed_at)
        self.assertFalse(r.authorize_edition)
        s = Sejours.objects.get(reservation=r)
        self.assertEqual((s.arrival_date, s.departure_date, s.price, s.confirmed), (self.arrival, None, 20, True))

    def test_sans_personne_refuse(self):
        resp = self.post()
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Reservations.objects.exists())

    def test_groupe_cree_n_personnes(self):
        resp = self.post(
            groupe='on', nom_groupe='Scouts', contact_email='chef@example.com',
            groupe_profile=self.profile.id, number_visitors=3,
            departure_date=(self.arrival + timedelta(days=2)).isoformat(),
        )
        self.assertEqual(resp.status_code, 302)
        r = Reservations.objects.get()
        self.assertEqual(r.max_visitors, 3)
        prenoms = sorted(Sejours.objects.filter(reservation=r).values_list('visitor__prenom', flat=True))
        self.assertEqual(prenoms, ['Personne 1', 'Personne 2', 'Personne 3'])


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class SejourActionsTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', email='a@example.com', password='x')
        self.client.force_login(self.admin)
        r = _reservation()
        v = Visitors.objects.create(nom='Dupont', prenom='Jean', confirmed=False)
        self.arrival = date.today() + timedelta(days=1)
        self.sejour = Sejours.objects.create(
            reservation=r, visitor=v, arrival_date=self.arrival,
            departure_date=self.arrival + timedelta(days=10), price=20, confirmed=True,
        )

    def url(self, name, sejour=None):
        return reverse(f'viale_manager:viale_manager_sejours_action_{name}', args=[(sejour or self.sejour).id])

    def post(self, name, sejour=None, **data):
        return self.client.post(self.url(name, sejour), {'_form_submitted': 'on', **data})

    def test_dialog_s_affiche_avec_les_dates(self):
        resp = self.client.get(self.url('edit_dates'))
        self.assertContains(resp, self.arrival.isoformat())

    def test_modifier_les_dates(self):
        resp = self.post('edit_dates', arrival_date=self.arrival.isoformat(), departure_date='')
        self.assertIn('HX-Redirect', resp.headers)
        self.sejour.refresh_from_db()
        self.assertIsNone(self.sejour.departure_date)

    def test_ajouter_une_absence(self):
        begin, end = self.arrival + timedelta(days=3), self.arrival + timedelta(days=5)
        resp = self.post('add_break', begin=begin.isoformat(), end=end.isoformat())
        self.assertIn('HX-Redirect', resp.headers)
        premier, reprise = Sejours.objects.order_by('arrival_date')
        self.assertEqual((premier.arrival_date, premier.departure_date), (self.arrival, begin))
        self.assertEqual((reprise.arrival_date, reprise.departure_date), (end, self.arrival + timedelta(days=10)))
        self.assertEqual((reprise.visitor_id, reprise.price, reprise.confirmed), (premier.visitor_id, 20, True))

    def test_absence_hors_du_sejour_refusee(self):
        resp = self.post('add_break', begin=self.arrival.isoformat(), end=(self.arrival + timedelta(days=20)).isoformat())
        self.assertNotIn('HX-Redirect', resp.headers)
        self.assertEqual(Sejours.objects.count(), 1)

    def test_annuler(self):
        self.post('cancel')
        self.assertFalse(Sejours.objects.exists())

    def test_sejour_termine_non_annulable_sauf_superuser(self):
        from django.contrib.auth.models import Permission

        self.sejour.arrival_date = date.today() - timedelta(days=10)
        self.sejour.departure_date = date.today() - timedelta(days=5)
        self.sejour.save()
        staff = User.objects.create_user(username='accueil', password='x', is_staff=True)
        staff.user_permissions.add(*Permission.objects.filter(codename__in=['view_sejours', 'delete_sejours']))
        self.client.force_login(staff)
        self.post('cancel')
        self.assertTrue(Sejours.objects.exists())
