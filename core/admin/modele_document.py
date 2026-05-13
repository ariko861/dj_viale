from django.contrib import admin
from unfold.admin import ModelAdmin

from core.models import ModeleDocument, TagDocument


@admin.register(TagDocument)
class TagDocumentAdmin(ModelAdmin):
    pass


@admin.register(ModeleDocument)
class ModeleDocumentAdmin(ModelAdmin):
    list_display = ['nom', 'tag']
    filter_horizontal = ['organes']