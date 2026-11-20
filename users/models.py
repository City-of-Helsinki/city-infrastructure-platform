import uuid
from typing import Optional, Tuple, TYPE_CHECKING

from auditlog.registry import auditlog
from django.contrib.auth.models import Group
from django.contrib.sessions.base_session import AbstractBaseSession
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from helusers.models import AbstractUser

from admin_helper.decorators import requires_fields

if TYPE_CHECKING:
    from traffic_control.models import ResponsibleEntity
    from users.session_store import SessionStore


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bypass_operational_area = models.BooleanField(
        verbose_name=_("Bypass operational area"),
        default=False,
        help_text=_("Disable operational area permission checks for this user."),
    )
    operational_areas = models.ManyToManyField(
        "traffic_control.OperationalArea",
        related_name="users",
        verbose_name=_("Operational areas"),
        blank=True,
        help_text=_("Operational areas, on which this user has permission to modify devices in."),
    )
    bypass_responsible_entity = models.BooleanField(
        verbose_name=_("Bypass responsible entity"),
        default=False,
        help_text=_("Disable responsible entity permission checks for this user."),
    )
    responsible_entities = models.ManyToManyField(
        "traffic_control.ResponsibleEntity",
        related_name="users",
        verbose_name=_("Responsible entities"),
        blank=True,
        help_text=_(
            "Responsible entities that this user is belongs to. "
            "This gives the users write permission to devices that belong to the Responsible Entities "
            "or any Responsible Entity that's hierarchically under the selected ones."
        ),
    )
    additional_information = models.TextField(
        _("Additional information"),
        blank=True,
        null=False,
        default="",
        help_text=_("Additional information related to this user."),
    )
    reactivated_at = models.DateTimeField(
        verbose_name=_("Reactivated at"),
        null=True,
        blank=True,
        help_text=_("Timestamp when admin manually reactivated this user account. Prevents automatic deactivation."),
    )
    receives_admin_notification_emails = models.BooleanField(
        verbose_name=_("Receives admin notification emails"),
        default=False,
        help_text=_(
            "If enabled, this user will receive admin notification emails about user deactivations "
            "and system events. Only users with valid email addresses will receive notifications."
        ),
    )

    def location_is_in_operational_area(self, location):
        """
        Check if given location is within the operational area defined for user
        """
        if self.is_superuser or self.bypass_operational_area:
            return True

        groups = Group.objects.filter(user=self).prefetch_related("operational_area", "operational_area__areas")
        return (
            self.operational_areas.filter(location__contains=location).exists()
            or groups.filter(operational_area__areas__location__contains=location).exists()
        )

    def has_bypass_responsible_entity_permission(self):
        return self.is_superuser or self.bypass_responsible_entity

    def has_activation_status_change_permission(self):
        return self.is_superuser

    def can_create_responsible_entity_devices(self):
        from traffic_control.models import GroupResponsibleEntity

        return (
            self.has_bypass_responsible_entity_permission()
            or self.responsible_entities.exists()
            or GroupResponsibleEntity.objects.filter(group__in=self.groups.all())
            .values("responsible_entities")
            .exists()
        )

    def has_responsible_entity_permission(self, responsible_entity: Optional["ResponsibleEntity"]) -> bool:
        """
        Check if user has permissions to edit given device based on ResponsibleEntity
        """
        if self.has_bypass_responsible_entity_permission() or responsible_entity is None:
            return True

        return (
            responsible_entity.get_ancestors(include_self=True)
            .filter(Q(users=self) | Q(groups__group__in=self.groups.all()))
            .exists()
        )

    def is_oidc_user(self) -> bool:
        """
        Check if user can authenticate via Azure AD (OIDC through Tunnistamo).

        Returns:
            bool: True if user has a social auth association with Tunnistamo provider.
        """
        return self.social_auth.filter(provider="tunnistamo").exists()

    def is_local_user(self) -> bool:
        """
        Check if user can authenticate via local password.

        Returns:
            bool: True if user has a usable password set.
        """
        return self.has_usable_password()

    def get_auth_type(self) -> Tuple[str, Optional[str]]:
        """
        Get user's authentication type with display color.

        Returns:
            Tuple[str, Optional[str]]: Display text and color code.
                - ("Local", "red") for password-only authentication
                - ("Azure AD", "green") for OIDC-only authentication
                - ("Both", "chocolate") for both authentication methods
                - ("None", None) for no authentication method
        """
        has_local = self.is_local_user()
        has_oidc = self.is_oidc_user()

        if has_local and has_oidc:
            return ("Both", "chocolate")
        if has_local:
            return ("Local", "red")
        if has_oidc:
            return ("Azure AD", "green")
        return ("None", None)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    # NOTE (2026-02-17 thiago) declare field dependencies so suggest_queryset_optimizations can introspect this
    @requires_fields("email", "first_name", "last_name")
    def __str__(self):
        return super().__str__()


class UserDeactivationStatus(models.Model):
    """
    Tracks the deactivation status and email notification history for inactive users.

    This model maintains the state of the user deactivation workflow, including
    timestamps for when warning emails were sent and when the user was deactivated.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="deactivation_status",
        verbose_name=_("User"),
    )
    one_month_email_sent_at = models.DateTimeField(
        verbose_name=_("One month warning email sent at"),
        null=True,
        blank=True,
        help_text=_("Timestamp when the 30-day warning email was sent."),
    )
    one_week_email_sent_at = models.DateTimeField(
        verbose_name=_("One week warning email sent at"),
        null=True,
        blank=True,
        help_text=_("Timestamp when the 7-day warning email was sent."),
    )
    one_day_email_sent_at = models.DateTimeField(
        verbose_name=_("One day warning email sent at"),
        null=True,
        blank=True,
        help_text=_("Timestamp when the 1-day warning email was sent."),
    )
    deactivated_at = models.DateTimeField(
        verbose_name=_("Deactivated at"),
        null=True,
        blank=True,
        help_text=_("Timestamp when the user was deactivated."),
    )

    class Meta:
        verbose_name = _("User Deactivation Status")
        verbose_name_plural = _("User Deactivation Statuses")
        db_table = "user_deactivation_status"

    def __str__(self) -> str:
        """
        String representation of the deactivation status.

        Returns:
            str: User's username with deactivation status.
        """
        status = "deactivated" if self.deactivated_at else "pending"
        return f"{self.user.username} - {status}"


class UserSession(AbstractBaseSession):
    """Database-backed session that records which user it belongs to.

    Replaces the default ``django.contrib.sessions`` model so that a user's sessions can be listed and
    terminated without decoding every session in the database. The extra columns are copied from the
    session data on every save by ``users.session_store.SessionStore``.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sessions",
        verbose_name=_("User"),
    )
    user_agent = models.CharField(_("User agent"), max_length=512, blank=True)
    logged_in_at = models.DateTimeField(_("Logged in at"), null=True, blank=True)

    class Meta(AbstractBaseSession.Meta):
        verbose_name = _("User session")
        verbose_name_plural = _("User sessions")

    def __str__(self) -> str:
        """Returns a description that does not reveal the session key.

        The inherited ``__str__`` returns the session key, which is a credential. It would be shown, for
        example, on the admin's delete confirmation page of a user, which lists the objects to be deleted.

        Returns:
            str: The session's public identifier, shortened.
        """
        from users.sessions import session_public_id

        return session_public_id(self.session_key)[:8]

    @classmethod
    def get_session_store_class(cls) -> type["SessionStore"]:
        """Returns the session store class that uses this model.

        Returns:
            type: The ``users.session_store.SessionStore`` class.
        """
        from users.session_store import SessionStore

        return SessionStore


auditlog.register(
    User,
    m2m_fields={"operational_areas", "responsible_entities", "groups", "ad_groups", "user_permissions"},
    mask_fields={"first_name", "last_name", "email"},
)
