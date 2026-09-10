from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from traffic_control.models import SearchOrphanFilesRunInfo


@admin.register(SearchOrphanFilesRunInfo)
class SearchOrphanFilesRunInfoAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            _("Schedule"),
            {"fields": ("started_at", "completed_at")},
        ),
        (
            _("Execution log"),
            {"fields": ("execution_log",)},
        ),
    )
    list_filter = ("started_at",)

    def has_add_permission(self, request):
        """Disable adding revert files through admin.
        https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.has_add_permission
        """
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Disable editing existing revert files through admin.
        https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.has_change_permission
        """
        return False
