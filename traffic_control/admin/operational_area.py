from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _

from ..constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from ..models import GroupOperationalArea, OperationalArea


class GroupOperationalAreaInline(admin.StackedInline):
    model = GroupOperationalArea
    can_delete = False
    verbose_name_plural = _("Operational areas")
    filter_horizontal = ("areas",)


class GroupAdmin(BaseGroupAdmin):
    inlines = (GroupOperationalAreaInline,)


class OperationalAreaAdmin(admin.OSMGeoAdmin):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    list_display = [
        "name",
        "id",
        "area_type",
        "contractor",
        "status",
    ]
    readonly_fields = [
        "source_name",
        "source_id",
    ]
    list_filter = ("area_type", "contractor", "status")


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
admin.site.register(OperationalArea, OperationalAreaAdmin)
