from django.contrib import admin
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from core.models import Adresse, Membre


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



@admin.register(Membre)
class MembreAdmin(ImportExportModelAdmin, ModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    resource_classes = [MembreResource]

    list_display = ['nom', 'prenom', 'email', 'telephone']
    search_fields = ['nom', 'prenom', 'email']