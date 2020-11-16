from django.contrib.gis import admin

from traffic_control.models import OperationType


@admin.register(OperationType)
class OperationTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "traffic_sign",
        "additional_sign",
        "road_marking",
        "barrier",
        "signpost",
        "traffic_light",
        "mount",
    )


class TrafficControlOperationInlineBase(admin.TabularInline):
    extra = 0
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at")
