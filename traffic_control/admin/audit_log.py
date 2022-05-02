from auditlog.admin import LogEntryAdmin
from auditlog.models import LogEntry
from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.http import HttpResponseRedirect
from django.urls import reverse

from traffic_control.admin.utils import CustomDateFieldListFilter

__all__ = ("AuditLogHistoryAdmin",)


class AuditLogHistoryAdmin(admin.ModelAdmin):
    def history_view(self, request, object_id, extra_context=None):
        return HttpResponseRedirect(
            "{url}?object_repr={object_repr}".format(
                url=reverse("admin:auditlog_logentry_changelist", args=()),
                object_repr=self.get_object(request, unquote(object_id)),
            )
        )


class CustomLogEntryAdmin(LogEntryAdmin):
    list_filter = [
        *LogEntryAdmin.list_filter,
        ("timestamp", CustomDateFieldListFilter),
    ]


admin.site.unregister(LogEntry)
admin.site.register(LogEntry, CustomLogEntryAdmin)
