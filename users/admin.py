from datetime import datetime, timedelta

from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin, UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.contrib.gis import admin
from django.utils import timezone
from django.utils.formats import localize
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from traffic_control.admin.operational_area import GroupOperationalAreaInline
from traffic_control.admin.responsible_entity import GroupResponsibleEntityInline

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
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "last_login_highlighted",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    @admin.display(description=_("last login"), ordering="last_login")
    def last_login_highlighted(self, obj: User):
        """
        The last login time of the User is highlighted if it was too long ago and the User is "active".
        """
        last_login = obj.last_login
        is_active = obj.is_active

        if not isinstance(last_login, datetime):
            return last_login

        time_since_last_login = timezone.now() - last_login

        # TODO: Time threshold could be configurable
        if is_active and time_since_last_login > timedelta(days=365):
            message = _("User is active, but last login was %(days)d days ago" % {"days": time_since_last_login.days})
            localized_last_login = localize(timezone.localtime(last_login))

            return format_html(
                '<span title="{}", style="color: var(--error-fg);">{}</span>',
                message,
                localized_last_login,
            )
        else:
            return last_login


admin.site.register(User, UserAdmin)


class GroupAdmin(BaseGroupAdmin):
    inlines = (
        GroupOperationalAreaInline,
        GroupResponsibleEntityInline,
    )


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
