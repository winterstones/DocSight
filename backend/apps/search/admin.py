from django.contrib import admin
from .models import SearchAuditLog, DocumentAlert


@admin.register(SearchAuditLog)
class SearchAuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "query", "results_count", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "query")
    readonly_fields = ("user", "query", "results_count", "created_at")

    def has_add_permission(self, request):
        return False


@admin.register(DocumentAlert)
class DocumentAlertAdmin(admin.ModelAdmin):
    list_display = ("user", "tag", "is_active", "created_at")
    list_filter = ("is_active", "created_at", "tag")
    search_fields = ("user__username", "tag__name")
