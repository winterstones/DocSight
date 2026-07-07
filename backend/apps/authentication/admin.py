from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserProfile, Tag


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "first_name", "last_name", "email")
    
    fieldsets = DefaultUserAdmin.fieldsets + (
        (_("Role Information"), {"fields": ("role",)}),
    )
    add_fieldsets = DefaultUserAdmin.add_fieldsets + (
        (_("Role Information"), {"fields": ("role",)}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "get_allowed_tags")
    search_fields = ("user__username", "user__email")
    filter_horizontal = ("allowed_tags",)

    def get_allowed_tags(self, obj):
        return ", ".join([tag.name for tag in obj.allowed_tags.all()])
    get_allowed_tags.short_description = "Allowed Tags"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
