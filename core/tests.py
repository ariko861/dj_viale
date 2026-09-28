from django.test import TestCase, override_settings

from core.models import User


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class GroupAdminTests(TestCase):

    def test_bouton_ajouter_un_groupe(self):
        self.client.force_login(User.objects.create_superuser(username='admin', password='x'))
        self.assertContains(self.client.get('/admin/auth/group/'), 'href="/admin/auth/group/add/"')


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class UserAdminTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', password='x')
        self.client.force_login(self.admin)

    def test_creation_hache_le_mot_de_passe(self):
        self.client.post('/admin/core/user/add/', {
            'username': 'nouveau', 'password1': 'Un-mot-de-passe-solide', 'password2': 'Un-mot-de-passe-solide',
            'usable_password': 'true',
        })
        user = User.objects.get(username='nouveau')
        self.assertTrue(user.check_password('Un-mot-de-passe-solide'))

    def test_modification_sans_champ_mot_de_passe_editable(self):
        resp = self.client.get(f'/admin/core/user/{self.admin.pk}/change/')
        self.assertNotContains(resp, 'name="password"')
        self.assertContains(resp, 'name="membre"')
        self.assertContains(resp, 'href="../password/"')


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class HijackTests(TestCase):

    def setUp(self):
        from viale_manager.models import Visitors

        self.visiteur = User.objects.create_user(username='jean@example.com')
        Visitors.objects.create(nom='Dupont', prenom='Jean', confirmed=False, user=self.visiteur)

    def test_superuser_se_fait_passer_pour_un_visiteur(self):
        self.client.force_login(User.objects.create_superuser(username='admin', password='x'))
        self.assertContains(self.client.get('/admin/core/user/'), f'data-hijack-user="{self.visiteur.pk}"')

        resp = self.client.post('/hijack/acquire/', {'user_pk': self.visiteur.pk, 'next': '/viale/compte/'})
        self.assertRedirects(resp, '/viale/compte/')
        page = self.client.get('/viale/compte/')
        self.assertContains(page, 'Jean Dupont')
        self.assertContains(page, '/hijack/release/')

        self.assertContains(page, 'Revenir à mon compte')
        self.client.post('/hijack/release/', {'next': '/admin/'})
        self.assertEqual(self.client.get('/admin/').status_code, 200)

    def test_bandeau_sur_l_admin_viale(self):
        # Sur /accueil/, current_app vaut 'viale_manager' : le lien de retour ne doit pas en dépendre.
        staff = User.objects.create_user(username='equipe', password='x', is_staff=True)
        self.client.force_login(User.objects.create_superuser(username='admin', password='x'))
        self.client.post('/hijack/acquire/', {'user_pk': staff.pk})
        page = self.client.get('/accueil/')
        self.assertContains(page, 'Revenir à mon compte')
        self.assertContains(page, 'value="/admin/core/user/"')

    def test_equipe_ne_peut_pas_se_faire_passer_pour_quelqu_un(self):
        self.client.force_login(User.objects.create_user(username='accueil', password='x', is_staff=True))
        resp = self.client.post('/hijack/acquire/', {'user_pk': self.visiteur.pk})
        self.assertEqual(resp.status_code, 403)


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class AnneeTests(TestCase):

    def setUp(self):
        from datetime import datetime

        from django.core.files.base import ContentFile

        from core.models import DocumentReunion, Organe, Reunion

        self.organe = Organe.objects.create(code='CA', nom="Conseil d'administration", nom_court='CA')
        self.reunion = Reunion.objects.create(organe=self.organe, debut=datetime(2025, 3, 10, 18))
        self.doc = DocumentReunion.objects.create(
            reunion=self.reunion, nom='pv.pdf', fichier=ContentFile(b'pv', name='pv.pdf'),
        )
        self.global_2025 = DocumentReunion.objects.create(
            annee=2025, nom='comptes.pdf', fichier=ContentFile(b'comptes', name='comptes.pdf'),
        )
        self.global_2026 = DocumentReunion.objects.create(
            annee=2026, nom='budget.pdf', fichier=ContentFile(b'budget', name='budget.pdf'),
        )

    def test_annee_par_defaut_depuis_debut(self):
        self.assertEqual(self.reunion.annee, 2025)

    def test_document_reprend_annee_de_la_reunion(self):
        self.assertEqual(self.doc.annee, 2025)
        self.doc.annee = 2030
        self.doc.save()
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.annee, 2025)

    def test_changer_annee_reunion_propage_aux_documents(self):
        self.reunion.annee = 2024
        self.reunion.save()
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.annee, 2024)

    def test_detacher_un_document_de_sa_reunion(self):
        self.client.force_login(User.objects.create_superuser(username='admin', password='x'))
        url = f'/admin/core/documentreunion/{self.doc.pk}/change/'
        self.assertContains(self.client.get(url), 'name="reunion"')
        resp = self.client.post(url, {'nom': 'pv.pdf', 'reunion': ''})
        self.assertEqual(resp.status_code, 302)
        self.doc.refresh_from_db()
        self.assertIsNone(self.doc.reunion)
        self.assertEqual(self.doc.annee, 2025)
        self.assertTrue(self.doc.fichier)

    def test_zip_des_documents_d_une_annee(self):
        import io
        import zipfile

        from core.models import DocumentReunion

        self.client.force_login(User.objects.create_superuser(username='admin', password='x'))
        ids = DocumentReunion.objects.filter(annee=2025).values_list('pk', flat=True)
        resp = self.client.post('/admin/core/documentreunion/', {
            'action': 'telecharger_zip', '_selected_action': list(ids),
        })
        self.assertEqual(resp['Content-Disposition'], 'attachment; filename="documents_2025.zip"')
        noms = zipfile.ZipFile(io.BytesIO(resp.content)).namelist()
        self.assertCountEqual(noms, [
            "2025/Conseil d'administration/2025-03-10 - CA/pv.pdf",
            '2025/Documents généraux/comptes.pdf',
        ])

    def test_onglets_annees(self):
        self.client.force_login(User.objects.create_superuser(username='admin', password='x'))
        resp = self.client.get('/admin/core/documentreunion/?annee=2026')
        self.assertContains(resp, 'href="/admin/core/documentreunion/?annee=2025"')
        self.assertContains(resp, 'href="/admin/core/documentreunion/?annee=2026"')
        onglets = {i['title']: i['active'] for i in resp.context['tab_list'][1]['items']}
        self.assertEqual(onglets, {'Toutes': False, '2026': True, '2025': False})
        self.assertContains(self.client.get('/admin/core/reunion/'), 'href="/admin/core/reunion/?annee=2025"')

    def test_filtre_par_annee_dans_l_admin(self):
        self.client.force_login(User.objects.create_superuser(username='admin', password='x'))
        self.assertEqual(self.client.get('/admin/core/reunion/?annee=2025').status_code, 200)
        resp = self.client.get('/admin/core/documentreunion/?annee=2026')
        self.assertContains(resp, 'budget.pdf')
        self.assertNotContains(resp, 'comptes.pdf')


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class AccesTests(TestCase):

    def setUp(self):
        import tempfile
        from datetime import datetime

        from core.models import DocumentReunion, Organe, Reunion

        media = tempfile.TemporaryDirectory()
        self.addCleanup(media.cleanup)
        self.enterContext(override_settings(MEDIA_ROOT=media.name))

        organe = Organe.objects.create(code='CA', nom="Conseil d'administration")
        self.reunion = Reunion.objects.create(organe=organe, debut=datetime(2025, 3, 10, 18))
        from django.core.files.base import ContentFile
        self.doc = DocumentReunion.objects.create(
            reunion=self.reunion, nom='pv.pdf', fichier=ContentFile(b'pv', name='pv.pdf'),
        )
        self.staff = User.objects.create_user(username='accueil', password='x', is_staff=True)

    def donner(self, *codenames):
        from django.contrib.auth.models import Permission

        self.staff.user_permissions.add(*Permission.objects.filter(codename__in=codenames))

    def test_ical_et_document_genere(self):
        urls = [f'/reunions/{self.reunion.pk}/ical/', f'/reunions/{self.reunion.pk}/documents/1/']
        for url in urls:
            self.assertRedirects(self.client.get(url), f'/admin/login/?next={url}', fetch_redirect_response=False)
        self.client.force_login(self.staff)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403)
        self.donner('view_reunion')
        self.assertEqual(self.client.get(urls[0]).status_code, 200)
        self.assertEqual(self.client.get(urls[1]).status_code, 404)  # pas de modèle : la vue est atteinte

    def test_media_selon_le_dossier(self):
        url = '/media/' + self.doc.fichier.name
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.donner('view_documentreunion')
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_media_dossier_inconnu_reserve_aux_superusers(self):
        import os

        from django.conf import settings

        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'autre'))
        with open(os.path.join(settings.MEDIA_ROOT, 'autre', 'x.txt'), 'w') as f:
            f.write('x')
        self.donner('view_documentreunion', 'view_modeledocument', 'view_procuration')
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get('/media/autre/x.txt').status_code, 403)
        self.client.force_login(User.objects.create_superuser(username='admin', password='x'))
        self.assertEqual(self.client.get('/media/autre/x.txt').status_code, 200)

    def test_document_non_public_refuse_aux_comptes_visiteurs(self):
        url = f'/documents/{self.doc.token}/'
        self.client.force_login(User.objects.create_user(username='visiteur@example.com'))
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_envoyer_email_demande_la_modification(self):
        url = f'/admin/core/reunion/{self.reunion.pk}/email/'
        self.donner('view_reunion')
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertNotContains(self.client.get(f'/admin/core/reunion/{self.reunion.pk}/change/'), 'Envoyer un email')
        self.donner('change_reunion')
        self.assertEqual(self.client.get(url).status_code, 200)
