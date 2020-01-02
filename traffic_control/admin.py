from django.contrib.gis import admin

from .models import Lifecycle, TrafficSignCode, TrafficSignPlan


@admin.register(TrafficSignPlan)
class TrafficSignPlanAdmin(admin.OSMGeoAdmin):
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
