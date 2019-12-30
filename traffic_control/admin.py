from django.contrib.gis import admin

from .models import TrafficSignPlan


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
