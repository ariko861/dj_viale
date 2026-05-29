from unfold.admin import ModelAdmin

from viale_manager.models import Visitors
from .site import viale_admin


class VisitorAdmin(ModelAdmin):
    search_fields = ['nom', 'prenom', 'email']
    list_display = ['nom', 'prenom', 'email', 'phone', 'confirmed']
    list_filter = ['confirmed']
    readonly_fields = ['created_at', 'updated_at']


viale_admin.register(Visitors, VisitorAdmin)