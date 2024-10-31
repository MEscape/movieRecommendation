from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()

class UserAdmin(BaseUserAdmin):
    model = User

    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': 'role'}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': 'role'}),
    )

admin.site.register(User)
