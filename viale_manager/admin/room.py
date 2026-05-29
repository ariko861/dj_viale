from unfold.admin import ModelAdmin, TabularInline

from viale_manager.models import Houses, Rooms
from .site import viale_admin


class RoomsInline(TabularInline):
    model = Rooms
    extra = 0
    tab = True
    fields = ['name', 'beds']


class HouseAdmin(ModelAdmin):
    list_display = ['name', 'community', 'displayhousenamewithroom']
    list_filter = ['community']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [RoomsInline]


class RoomAdmin(ModelAdmin):
    list_display = ['name', 'house', 'beds']
    list_filter = ['house']
    search_fields = ['name']
    autocomplete_fields = ['house']
    readonly_fields = ['created_at', 'updated_at']


viale_admin.register(Houses, HouseAdmin)
viale_admin.register(Rooms, RoomAdmin)