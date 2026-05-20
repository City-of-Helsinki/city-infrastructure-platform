from auditlog.admin import LogEntryAdmin
from auditlog.models import LogEntry
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.contrib.admin.utils import unquote
from django.http import HttpResponseRedirect
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from traffic_control.admin.admin_filters import CustomDateFieldListFilter

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
        ("actor", RelatedOnlyFieldListFilter),
        "actor__groups",
    ]

    @admin.display(description=_("User"))
    def user_url(self, obj):
        if obj.actor:
            app_label, model = settings.AUTH_USER_MODEL.split(".")
            try:
                link = reverse(f"admin:{app_label}_{model.lower()}_change", args=[obj.actor.pk])
            except NoReverseMatch:
                return str(obj.actor)
            return format_html('<a href="{}">{}</a>', link, obj.actor)

        return "None (deleted or old management command)"


admin.site.unregister(LogEntry)
admin.site.register(LogEntry, CustomLogEntryAdmin)
