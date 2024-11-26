from django.contrib.gis import admin

from traffic_control.constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from traffic_control.forms import CoverageAreaModelForm
from traffic_control.models import CoverageArea, CoverageAreaCategory


@admin.register(CoverageAreaCategory)
class CoverageAreaCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(CoverageArea)
class CoverageAreaAdmin(admin.GISModelAdmin):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    form = CoverageAreaModelForm
    list_select_related = ("category",)
    list_display = [
        "id",
        "category",
        "area_type",
        "validity",
        "duration",
        "parking_slots",
    ]
    readonly_fields = [
        "source_name",
        "source_id",
    ]
    list_filter = ("category", "area_type")
