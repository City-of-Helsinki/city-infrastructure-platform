from datetime import datetime, timedelta

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin, UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Exists, OuterRef
from django.utils import timezone
from django.utils.formats import localize
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from social_django.models import UserSocialAuth

from traffic_control.admin.operational_area import GroupOperationalAreaInline
from traffic_control.admin.responsible_entity import GroupResponsibleEntityInline

from .models import User


class AuthenticationTypeFilter(admin.SimpleListFilter):
    """
    Filter users by their authentication type (Local, Azure AD, Both, or None).
    """

    title = _("authentication type")
    parameter_name = "auth_type"

    def lookups(self, request, model_admin):
        """
        Define filter options.

        Args:
            request: The current request object.
            model_admin: The model admin instance.

        Returns:
            list: List of tuples (value, label) for filter options.
        """
        return [
            ("local", _("Local")),
            ("oidc", _("Azure AD")),
            ("both", _("Both")),
            ("none", _("None")),
        ]

    def queryset(self, request, queryset):
        """
        Filter queryset based on selected authentication type.

        Args:
            request: The current request object.
            queryset: The queryset to filter.

        Returns:
            QuerySet: Filtered queryset based on authentication type.
        """
        value = self.value()
        if not value:
            return queryset

        # Annotate queryset with has_oidc field
        has_social_auth = Exists(UserSocialAuth.objects.filter(user=OuterRef("pk"), provider="tunnistamo"))
        queryset = queryset.annotate(has_oidc=has_social_auth)

        if value == "local":
            # Password only: has usable password AND no social auth
            return queryset.filter(has_oidc=False).exclude(password__startswith="!")

        if value == "oidc":
            # Azure AD only: has social auth AND no usable password
            return queryset.filter(has_oidc=True, password__startswith="!")

        if value == "both":
            # Both: has social auth AND has usable password
            return queryset.filter(has_oidc=True).exclude(password__startswith="!")

        if value == "none":
            # Neither: no social auth AND no usable password
            return queryset.filter(has_oidc=False, password__startswith="!")

        return queryset


class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            _("Authentication Type"),
            {
                "fields": ("auth_type_display",),
            },
        ),
        (_("Additional user information"), {"fields": ("additional_information",)}),
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
    readonly_fields = ("auth_type_display",)
    filter_horizontal = BaseUserAdmin.filter_horizontal + (
        "operational_areas",
        "responsible_entities",
    )
    list_display = (
        "username",
        "auth_type_display",
        "email",
        "first_name",
        "last_name",
        "last_login_highlighted",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    list_filter = BaseUserAdmin.list_filter + (AuthenticationTypeFilter,)

    def get_queryset(self, request):
        """
        Optimize queryset by prefetching social_auth relationships.

        Args:
            request: The current request object.

        Returns:
            QuerySet: Optimized queryset with prefetched social_auth.
        """
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("social_auth")

    @admin.display(description=_("Authentication Type"))
    def auth_type_display(self, obj: User) -> str:
        """
        Display authentication type with color coding.

        Args:
            obj (User): The user instance.

        Returns:
            str: HTML formatted authentication type with color.
        """
        text, color = obj.get_auth_type()
        if color:
            return format_html('<span style="color: {};">{}</span>', color, text)
        return text

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
