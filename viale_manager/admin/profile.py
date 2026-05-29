from unfold.admin import ModelAdmin

from viale_manager.models import Profiles
from .site import viale_admin


class ProfileAdmin(ModelAdmin):
    list_display = ['name', 'price', 'is_default', 'remarques']
    list_editable = ['price', 'is_default']
    readonly_fields = ['created_at', 'updated_at']


viale_admin.register(Profiles, ProfileAdmin)