from datetime import datetime, timedelta

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin, UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db import models as django_models, transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone
from django.utils.formats import localize
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from social_django.models import UserSocialAuth

from traffic_control.admin.operational_area import GroupOperationalAreaInline
from traffic_control.admin.responsible_entity import GroupResponsibleEntityInline

from .models import User, UserDeactivationStatus


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


class ReactivatedFilter(admin.SimpleListFilter):
    """
    Filter users by their reactivation date.
    """

    title = _("reactivated")
    parameter_name = "reactivated"

    def lookups(self, request: django_models.QuerySet, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        """
        Define filter options.

        Args:
            request: The current request object.
            model_admin: The model admin instance.

        Returns:
            list: List of tuples (value, label) for filter options.
        """
        return [
            ("30", _("Last 30 days")),
            ("90", _("Last 90 days")),
            ("180", _("Last 180 days")),
        ]

    def queryset(self, request: django_models.QuerySet, queryset: django_models.QuerySet) -> django_models.QuerySet:
        """
        Filter queryset based on selected reactivation timeframe.

        Args:
            request: The current request object.
            queryset: The queryset to filter.

        Returns:
            QuerySet: Filtered queryset based on reactivation date.
        """
        value = self.value()
        if not value:
            return queryset

        days = int(value)
        cutoff_date = timezone.now() - timedelta(days=days)
        return queryset.filter(reactivated_at__gte=cutoff_date)


class DeactivationStageFilter(admin.SimpleListFilter):
    """
    Filter users by their deactivation warning stage.

    Shows users who are in different stages of the deactivation workflow:
    - 30-day warning sent (150+ days inactive)
    - 7-day warning sent (173+ days inactive)
    - 1-day warning sent (179+ days inactive)
    - Deactivated (180+ days inactive)
    """

    title = _("deactivation stage")
    parameter_name = "deactivation_stage"

    def lookups(self, request, model_admin):
        """
        Define filter options for deactivation stages.

        Args:
            request: The current request object.
            model_admin: The model admin instance.

        Returns:
            list: List of tuples (value, label) for filter options.
        """
        return [
            ("30_day", _("30-day warning sent")),
            ("7_day", _("7-day warning sent")),
            ("1_day", _("1-day warning sent")),
            ("deactivated", _("Deactivated")),
        ]

    def queryset(self, request, queryset):
        """
        Filter queryset based on selected deactivation stage.

        Args:
            request: The current request object.
            queryset: The queryset to filter.

        Returns:
            QuerySet: Filtered queryset based on deactivation stage.
        """
        from users.models import UserDeactivationStatus

        value = self.value()
        if not value:
            return queryset

        # Subquery to check if user has deactivation status
        has_status = UserDeactivationStatus.objects.filter(user=OuterRef("pk"))

        if value == "30_day":
            # Users with 30-day warning sent but not yet 7-day warning
            return queryset.filter(
                Exists(has_status.filter(one_month_email_sent_at__isnull=False, one_week_email_sent_at__isnull=True))
            )
        elif value == "7_day":
            # Users with 7-day warning sent but not yet 1-day warning
            return queryset.filter(
                Exists(has_status.filter(one_week_email_sent_at__isnull=False, one_day_email_sent_at__isnull=True))
            )
        elif value == "1_day":
            # Users with 1-day warning sent but not yet deactivated
            return queryset.filter(
                Exists(has_status.filter(one_day_email_sent_at__isnull=False, deactivated_at__isnull=True))
            )
        elif value == "deactivated":
            # Users who have been deactivated
            return queryset.filter(Exists(has_status.filter(deactivated_at__isnull=False)))

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
            _("Activity Tracking"),
            {
                "fields": ("last_api_use",),
                "description": _(
                    "Track user's API usage activity. This field is automatically updated when the user uses the API."
                ),
            },
        ),
        (
            _("Reactivation"),
            {
                "fields": ("reactivated_at",),
            },
        ),
        (
            _("Admin Notifications"),
            {
                "fields": ("receives_admin_notification_emails",),
                "description": _(
                    "Configure whether this user receives admin notification emails about "
                    "user deactivations and system events."
                ),
            },
        ),
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
    readonly_fields = ("auth_type_display", "last_api_use", "reactivated_at")
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
        "last_api_use",
        "reactivated_at",
        "receives_admin_notification_emails",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    list_filter = BaseUserAdmin.list_filter + (
        AuthenticationTypeFilter,
        ReactivatedFilter,
        DeactivationStageFilter,
    )

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

    @admin.action(permissions=["change"], description=_("Reactivate selected users"))
    def reactivate_selected_users(self, request, queryset) -> None:
        """
        Admin action to reactivate selected users.

        This action sets is_active=True, updates reactivated_at timestamp, and deletes
        any associated UserDeactivationStatus records. Only superusers can perform this action.

        Args:
            request: The current HTTP request object.
            queryset: The queryset of selected users.
        """
        if not request.user.is_superuser:
            self.message_user(
                request,
                _("Only superusers can reactivate users."),
                level="error",
            )
            return

        count = 0
        with transaction.atomic():
            for user in queryset:
                user.is_active = True
                user.reactivated_at = timezone.now()
                user.save(update_fields=["is_active", "reactivated_at"])

                # Delete deactivation status if exists
                # Note: Signal may have already deleted it when reactivated_at was set
                try:
                    if hasattr(user, "deactivation_status"):
                        user.deactivation_status.delete()
                except (AttributeError, ValueError):
                    # Already deleted by signal or doesn't exist
                    pass

                count += 1

        self.message_user(
            request,
            _("Successfully reactivated %(count)d user(s).") % {"count": count},
            level="success",
        )

    actions = ["reactivate_selected_users"]


@admin.register(UserDeactivationStatus)
class UserDeactivationStatusAdmin(admin.ModelAdmin):
    """
    Admin interface for UserDeactivationStatus model.

    Displays deactivation workflow status and email notification history.
    Read-only interface to track the deactivation process.
    """

    list_display = [
        "user",
        "status_display",
        "one_month_email_sent_at",
        "one_week_email_sent_at",
        "one_day_email_sent_at",
        "deactivated_at",
    ]

    list_filter = [
        "deactivated_at",
        "one_month_email_sent_at",
        "one_week_email_sent_at",
        "one_day_email_sent_at",
    ]

    search_fields = [
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    ]

    readonly_fields = [
        "user",
        "one_month_email_sent_at",
        "one_week_email_sent_at",
        "one_day_email_sent_at",
        "deactivated_at",
        "status_display",
    ]

    ordering = ["-deactivated_at", "-one_day_email_sent_at"]

    date_hierarchy = "deactivated_at"

    def get_queryset(self, request):
        """
        Optimize queryset by selecting related user to avoid N+1 queries.

        Args:
            request: The current request object.

        Returns:
            QuerySet: Optimized queryset with selected user.
        """
        queryset = super().get_queryset(request)
        return queryset.select_related("user")

    @admin.display(description=_("Status"))
    def status_display(self, obj: UserDeactivationStatus) -> str:
        """
        Display the current status with color coding.

        Args:
            obj (UserDeactivationStatus): The deactivation status object.

        Returns:
            str: HTML formatted status string.
        """
        if obj.deactivated_at:
            return format_html('<span style="color: red; font-weight: bold;">DEACTIVATED</span>')
        elif obj.one_day_email_sent_at:
            return format_html('<span style="color: orange; font-weight: bold;">1-DAY WARNING SENT</span>')
        elif obj.one_week_email_sent_at:
            return format_html('<span style="color: #ff9800; font-weight: bold;">7-DAY WARNING SENT</span>')
        elif obj.one_month_email_sent_at:
            return format_html('<span style="color: #ffc107;">30-DAY WARNING SENT</span>')
        else:
            return format_html('<span style="color: gray;">PENDING</span>')

    def has_add_permission(self, request):
        """
        Disable manual creation - records are created automatically by management command.

        Args:
            request: The current request object.

        Returns:
            bool: Always False to prevent manual creation.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Only superusers can delete deactivation status records.

        Args:
            request: The current request object.
            obj: The object being checked (optional).

        Returns:
            bool: True if user is superuser, False otherwise.
        """
        return request.user.is_superuser


admin.site.register(User, UserAdmin)


class GroupAdmin(BaseGroupAdmin):
    inlines = (
        GroupOperationalAreaInline,
        GroupResponsibleEntityInline,
    )


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
