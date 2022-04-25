from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin, UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _

from city_furniture.admin.responsible_entity import GroupResponsibleEntityInline
from traffic_control.admin.operational_area import GroupOperationalAreaInline

from .models import User


class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            _("Operational area"),
            {
                "fields": (
                    "bypass_operational_area",
                    "operational_areas",
                )
            },
        ),
        (
            _("Responsible Entity"),
            {
                "fields": (
                    "bypass_responsible_entity",
                    "responsible_entities",
                )
            },
        ),
    )
    filter_horizontal = BaseUserAdmin.filter_horizontal + (
        "operational_areas",
        "responsible_entities",
    )


admin.site.register(User, UserAdmin)


class GroupAdmin(BaseGroupAdmin):
    inlines = (
        GroupOperationalAreaInline,
        GroupResponsibleEntityInline,
    )


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
