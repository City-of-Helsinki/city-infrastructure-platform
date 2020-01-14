from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _

from .models import Lifecycle, TrafficSignCode, TrafficSignPlan, TrafficSignReal

admin.site.site_header = _("City Infrastructure Platform Administration")


@admin.register(TrafficSignPlan)
class TrafficSignPlanAdmin(admin.OSMGeoAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "value",
        "lifecycle",
        "location_xy",
        "decision_date",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(TrafficSignReal)
class TrafficSignRealAdmin(admin.OSMGeoAdmin):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "value",
        "lifecycle",
        "location_xy",
        "installation_date",
    )
    ordering = ("-created_at",)
    actions = None


@admin.register(TrafficSignCode)
class TrafficSignCodeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "description",
    )
    ordering = ("-code",)
    actions = None


@admin.register(Lifecycle)
class LifecycleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "description",
    )
    ordering = ("-status",)
    actions = None
