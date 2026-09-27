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
