from django.contrib.gis import admin

from traffic_control.forms import CoverageAreaModelForm
from traffic_control.mixins import Geometry3DFieldAdminMixin
from traffic_control.models import CoverageArea, CoverageAreaCategory


@admin.register(CoverageAreaCategory)
class CoverageAreaCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(CoverageArea)
class CoverageAreaAdmin(Geometry3DFieldAdminMixin, admin.GISModelAdmin):
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
    list_filter = ("category", "area_type")
