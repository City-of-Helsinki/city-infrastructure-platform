import uuid
from typing import Optional, TYPE_CHECKING

from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from helusers.models import AbstractUser

if TYPE_CHECKING:
    from traffic_control.models import ResponsibleEntity


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bypass_operational_area = models.BooleanField(
        verbose_name=_("Bypass operational area"),
        help_text=_("Disable operational area permission checks for this user."),
        default=False,
    )
    operational_areas = models.ManyToManyField(
        "traffic_control.OperationalArea",
        related_name="users",
        verbose_name=_("Operational areas"),
        blank=True,
    )
    bypass_responsible_entity = models.BooleanField(
        verbose_name=_("Bypass responsible entity"),
        help_text=_("Disable responsible entity permission checks for this user."),
        default=False,
    )
    responsible_entities = models.ManyToManyField(
        "traffic_control.ResponsibleEntity",
        related_name="users",
        verbose_name=_("Responsible entities"),
        help_text=_(
            "Responsible entities that this user is belongs to. "
            "This gives the users write permission to devices that belong to the Responsible Entities "
            "or any Responsible Entity that's hierarchically under the selected ones."
        ),
        blank=True,
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

    def can_create_responsible_entity_devices(self):
        from traffic_control.models import GroupResponsibleEntity

        return (
            self.has_bypass_responsible_entity_permission()
            or self.responsible_entities.exists()
            or GroupResponsibleEntity.objects.filter(group__in=self.groups.all())
            .values("responsible_entities")
            .exists()
        )

    def has_responsible_entity_permission(self, responsible_entity: Optional["ResponsibleEntity"]):
        """
        Check if user has permissions to edit given device based on ResponsibleEntity
        """
        if self.has_bypass_responsible_entity_permission():
            return True

        if responsible_entity is None:
            return False

        return (
            responsible_entity.get_ancestors(include_self=True)
            .filter(Q(users=self) | Q(groups__group__in=self.groups.all()))
            .exists()
        )

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
