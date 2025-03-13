from django.contrib import admin

from traffic_control.models import ParkingZoneUpdateInfo


@admin.register(ParkingZoneUpdateInfo)
class ParkingZoneUpdateInfoAdmin(admin.ModelAdmin):
    list_display = ("id", "start_time", "end_time", "database_update")
    ordering = ("-start_time",)
