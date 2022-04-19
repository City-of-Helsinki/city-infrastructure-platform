from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

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
