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
        "traffic_control.OperationalArea", related_name="users", blank=True,
    )
