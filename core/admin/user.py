from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.urls import reverse
from hijack.contrib.admin import HijackUserAdminMixin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from core.models import User


# Les classes d'admin de Django (hachage du mot de passe, formulaire des
# permissions) sont combinées au ModelAdmin d'Unfold, sans lequel ses templates
# n'affichent pas certains éléments, comme le bouton « Ajouter ».
@admin.register(User)
class UserAdmin(HijackUserAdminMixin, BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    fieldsets = BaseUserAdmin.fieldsets + (('ASBL', {'fields': ('membre',)}),)
    autocomplete_fields = ['membre']

    def get_hijack_success_url(self, request, obj):
        # Bouton « Se faire passer pour » (superusers) : un compte visiteur arrive
        # sur « Mon compte », un membre de l'équipe sur l'admin.
        return reverse('admin:index') if obj.is_staff else reverse('compte')


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
