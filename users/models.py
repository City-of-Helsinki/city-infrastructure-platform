import uuid

from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import gettext_lazy as _
from helusers.models import AbstractUser


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

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
