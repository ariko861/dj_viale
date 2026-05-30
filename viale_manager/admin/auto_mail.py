from django.db import models
from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget

from viale_manager.models import AutoMails
from .site import viale_admin


class AutoMailAdmin(ModelAdmin):
    list_display = ['sujet', 'type', 'time_delta', 'actif']
    list_filter = ['type', 'actif']
    list_editable = ['actif']
    search_fields = ['sujet', 'body']
    readonly_fields = ['created_at', 'updated_at']
    formfield_overrides = {
        models.TextField: {'widget': WysiwygWidget},
    }


viale_admin.register(AutoMails, AutoMailAdmin)