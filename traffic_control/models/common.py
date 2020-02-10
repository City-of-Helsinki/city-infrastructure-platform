import uuid

from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _  # NOQA
from enumfields import Enum


class InstallationStatus(Enum):
    IN_USE = "IN_USE"
    COVERED = "COVERED"
    FALLEN = "FALLEN"
    MISSING = "MISSING"
    OTHER = "OTHER"

    class Labels:
        IN_USE = _("In use")
        COVERED = _("Covered")
        FALLEN = _("Fallen")
        MISSING = _("Missing")
        OTHER = _("Other")


class Size(Enum):
    SMALL = "S"
    MEDIUM = "M"
    LARGE = "L"

    class Labels:
        SMALL = _("Small")
        MEDIUM = _("Medium")
        LARGE = _("Large")


class Surface(Enum):
    CONVEX = "CONVEX"
    FLAT = "FLAT"

    class Labels:
        CONVEX = _("Convex")
        FLAT = _("Flat")


class Reflection(Enum):
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"

    class Labels:
        R1 = _("r1")
        R2 = _("r2")
        R3 = _("r3")


class Color(Enum):
    BLUE = 1
    YELLOW = 2

    class Labels:
        BLUE = _("Blue")
        YELLOW = _("Yellow")


class Lifecycle(Enum):
    ACTIVE = 1
    TEMPORARILY_ACTIVE = 2
    TEMPORARILY_INACTIVE = 3
    INACTIVE = 99

    class Labels:
        ACTIVE = _("Active")
        TEMPORARILY_ACTIVE = _("Temporarily active")
        TEMPORARILY_INACTIVE = _("Temporarily inactive")
        INACTIVE = _("Inactive")


class Condition(Enum):
    VERY_BAD = 1
    BAD = 2
    AVERAGE = 3
    GOOD = 4
    VERY_GOOD = 5

    class Labels:
        VERY_BAD = _("Very bad")
        BAD = _("Bad")
        AVERAGE = _("Average")
        GOOD = _("Good")
        VERY_GOOD = _("Very good")


class TrafficSignCode(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    code = models.CharField(_("Code"), unique=True, max_length=32)
    description = models.CharField(
        _("Description"), max_length=254, blank=True, null=True
    )

    class Meta:
        db_table = "traffic_sign_code"
        verbose_name = _("Traffic Sign Code")
        verbose_name_plural = _("Traffic Sign Codes")

    def __str__(self):
        return "%s - %s" % (self.code, self.description)
