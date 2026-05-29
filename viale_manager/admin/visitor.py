from unfold.admin import ModelAdmin

from viale_manager.models import Visitors
from .site import viale_admin


class VisitorAdmin(ModelAdmin):
    pass


viale_admin.register(Visitors, VisitorAdmin)