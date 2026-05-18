from django.contrib import admin
from unfold.admin import ModelAdmin

from core.models import ModeleDocument, TagDocument


@admin.register(TagDocument)
class TagDocumentAdmin(ModelAdmin):

    def has_module_permission(self, request):
        return False


@admin.register(ModeleDocument)
class ModeleDocumentAdmin(ModelAdmin):
    list_display = ['nom', 'tag']
    filter_horizontal = ['organes']