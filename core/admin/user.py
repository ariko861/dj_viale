from django.contrib import admin
from unfold.admin import ModelAdmin

from core.models import User


@admin.register(User)
class UserAdmin(ModelAdmin):
    pass