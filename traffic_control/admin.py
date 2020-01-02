from django.contrib.gis import admin
from django.contrib.gis.geos import Point

from .models import Lifecycle, TrafficSignCode, TrafficSignPlan


@admin.register(TrafficSignPlan)
class TrafficSignPlanAdmin(admin.OSMGeoAdmin):
    pnt = Point(24.945831, 60.192059, srid=4326)  # Helsinki city coordinates
    pnt.transform(900913)
    default_lon, default_lat = pnt.coords
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "location_xy",
        "decision_date",
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
