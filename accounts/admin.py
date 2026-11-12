from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "role", "phone", "is_active", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("email", "full_name", "phone")
    readonly_fields = ("password", "last_login", "date_joined")
    exclude = ("groups", "user_permissions")
