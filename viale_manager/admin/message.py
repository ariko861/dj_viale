from django.db import models
from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget

from viale_manager.models import Messages
from .site import viale_admin


class MessageAdmin(ModelAdmin):
    list_display = ['title', 'type']
    list_filter = ['type']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at', 'updated_at']
    formfield_overrides = {
        models.TextField: {'widget': WysiwygWidget},
    }


viale_admin.register(Messages, MessageAdmin)