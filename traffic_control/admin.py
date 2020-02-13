from django.contrib.admin.utils import unquote
from django.contrib.gis import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import (
    BarrierPlan,
    BarrierReal,
    MountPlan,
    MountReal,
    PortalType,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficSignCode,
    TrafficSignPlan,
    TrafficSignReal,
)

admin.site.site_header = _("City Infrastructure Platform Administration")


class AuditLogHistoryAdmin(admin.ModelAdmin):
    def history_view(self, request, object_id, extra_context=None):
        return HttpResponseRedirect(
            "{url}?object_repr={object_repr}".format(
                url=reverse("admin:auditlog_logentry_changelist", args=()),
                object_repr=self.get_object(request, unquote(object_id)),
            )
        )


@admin.register(BarrierPlan)
class BarrierPlanAdmin(admin.OSMGeoAdmin, AuditLogHistoryAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "type",
        "lifecycle",
        "location",
        "decision_date",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(BarrierReal)
class BarrierRealAdmin(admin.OSMGeoAdmin, AuditLogHistoryAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "type",
        "lifecycle",
        "location",
        "installation_date",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(TrafficLightPlan)
class TrafficLightPlanAdmin(admin.OSMGeoAdmin, AuditLogHistoryAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "txt",
        "lifecycle",
        "location",
        "decision_date",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(TrafficLightReal)
class TrafficLightRealAdmin(admin.OSMGeoAdmin, AuditLogHistoryAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "txt",
        "lifecycle",
        "location",
        "installation_date",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(TrafficSignPlan)
class TrafficSignPlanAdmin(admin.OSMGeoAdmin, AuditLogHistoryAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "value",
        "lifecycle",
        "location",
        "decision_date",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(TrafficSignReal)
class TrafficSignRealAdmin(admin.OSMGeoAdmin, AuditLogHistoryAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "value",
        "lifecycle",
        "location",
        "installation_date",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(SignpostPlan)
class SignpostPlanAdmin(admin.OSMGeoAdmin, AuditLogHistoryAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "txt",
        "lifecycle",
        "location",
        "decision_date",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(SignpostReal)
class SignpostRealAdmin(admin.OSMGeoAdmin, AuditLogHistoryAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "txt",
        "lifecycle",
        "location",
        "installation_date",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(MountPlan)
class MountPlanAdmin(admin.OSMGeoAdmin, AuditLogHistoryAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "type",
        "lifecycle",
        "location",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(MountReal)
class MountRealAdmin(admin.OSMGeoAdmin, AuditLogHistoryAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "type",
        "lifecycle",
        "location",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(RoadMarkingPlan)
class RoadMarkingPlanAdmin(admin.OSMGeoAdmin, AuditLogHistoryAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "lifecycle",
        "location",
        "decision_date",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(RoadMarkingReal)
class RoadMarkingRealAdmin(admin.OSMGeoAdmin, AuditLogHistoryAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "lifecycle",
        "location",
        "installation_date",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(TrafficSignCode)
class TrafficSignCodeAdmin(AuditLogHistoryAdmin):
    list_display = (
        "code",
        "description",
    )
    ordering = ("-code",)
    actions = None


@admin.register(PortalType)
class PortalTypeAdmin(AuditLogHistoryAdmin):
    list_display = (
        "structure",
        "build_type",
        "model",
    )
    ordering = ("structure", "build_type", "model")
    actions = None
