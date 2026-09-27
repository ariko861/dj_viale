from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from core.models import Adresse, Membre, User


class MembreResource(resources.ModelResource):
    adresse_adresse = fields.Field(column_name='adresse')
    adresse_ville = fields.Field(column_name='ville')
    adresse_code_postal = fields.Field(column_name='code_postal')

    class Meta:
        model = Membre
        fields = ('id', 'prenom', 'nom', 'email', 'telephone',
                  'adresse_adresse', 'adresse_ville', 'adresse_code_postal')
        export_order = fields

    def dehydrate_adresse_adresse(self, membre):
        return membre.adresse.adresse if membre.adresse else ''

    def dehydrate_adresse_ville(self, membre):
        return membre.adresse.ville if membre.adresse else ''

    def dehydrate_adresse_code_postal(self, membre):
        return membre.adresse.code_postal if membre.adresse else ''

    def before_save_instance(self, instance, row, **kwargs):
        rue = str(row.get('adresse') or '').strip()
        ville = str(row.get('ville') or '').strip()
        code_postal = str(row.get('code_postal') or '').strip()

        if not any([rue, ville, code_postal]):
            return

        if instance.adresse_id:
            Adresse.objects.filter(pk=instance.adresse_id).update(
                adresse=rue, ville=ville, code_postal=code_postal,
            )
        else:
            instance.adresse = Adresse.objects.create(
                adresse=rue, ville=ville, code_postal=code_postal,
            )


@admin.register(Membre)
class MembreAdmin(ImportExportModelAdmin, ModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    resource_classes = [MembreResource]

    list_display = ['nom', 'prenom', 'email', 'telephone']
    search_fields = ['nom', 'prenom', 'email']
    actions = ['envoyer_lien_mot_de_passe']

    @admin.action(description='Envoyer le lien de définition du mot de passe')
    def envoyer_lien_mot_de_passe(self, request, queryset):
        validite_jours = settings.PASSWORD_RESET_TIMEOUT // 86400
        envoyes = 0
        ignores = []

        for membre in queryset:
            if not membre.email:
                ignores.append(str(membre))
                continue

            try:
                user = membre.user
            except User.DoesNotExist:
                user = User(
                    username=membre.email,
                    email=membre.email,
                    first_name=membre.prenom,
                    last_name=membre.nom,
                    membre=membre,
                )
                user.set_unusable_password()
                user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            lien = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )

            corps = (
                f"Bonjour {membre.prenom},\n\n"
                "Un compte a été créé pour vous sur la plateforme de l'ASBL.\n"
                "Cliquez sur le lien ci-dessous pour définir votre mot de passe :\n\n"
                f"{lien}\n\n"
                f"Votre identifiant de connexion est : {user.username}\n\n"
                f"Ce lien est valable {validite_jours} jour(s)."
            )
            EmailMessage(
                subject='Définissez votre mot de passe',
                body=corps,
                to=[membre.email],
            ).send()
            envoyes += 1

        if envoyes:
            messages.success(request, f'Lien envoyé à {envoyes} membre(s).')
        if ignores:
            messages.warning(request, f"Ignoré(s) (pas d'email) : {', '.join(ignores)}")