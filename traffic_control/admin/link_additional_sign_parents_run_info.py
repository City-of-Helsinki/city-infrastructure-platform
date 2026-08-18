from django.contrib import admin

from traffic_control.models import LinkAdditionalSignParentsRunInfo


@admin.register(LinkAdditionalSignParentsRunInfo)
class LinkAdditionalSignParentsRunInfoAdmin(admin.ModelAdmin):
    list_display = ("id", "started_at", "completed_at", "dry_run")
    ordering = ("-started_at",)
