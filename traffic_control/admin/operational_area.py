from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _

from traffic_control.forms import OperationalModelForm
from traffic_control.mixins import Geometry3DFieldAdminMixin
from traffic_control.models import GroupOperationalArea, OperationalArea


class GroupOperationalAreaInline(admin.StackedInline):
    model = GroupOperationalArea
    can_delete = False
    verbose_name_plural = _("Operational areas")
    filter_horizontal = ("areas",)


class OperationalAreaAdmin(Geometry3DFieldAdminMixin, admin.GISModelAdmin):
    form = OperationalModelForm
    list_display = [
        "name",
        "id",
        "area_type",
        "contractor",
        "status",
    ]
    list_filter = ("area_type", "contractor", "status")


admin.site.register(OperationalArea, OperationalAreaAdmin)
