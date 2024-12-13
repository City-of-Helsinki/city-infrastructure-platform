from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

TRAFFIC_SIGN_TYPE_MAP = {
    "A": _("Warning sign"),
    "B": _("Priority or give-way sign"),
    "C": _("Prohibitory or restrictive sign"),
    "D": _("Mandatory sign"),
    "E": _("Regulatory sign"),
    "F": _("Information sign"),
    "G": _("Service sign"),
    "H": _("Additional sign"),
    "I": _("Other road sign"),
}
TRAFFIC_SIGN_TYPE_CHOICES = tuple((key, value) for key, value in TRAFFIC_SIGN_TYPE_MAP.items())


class Condition(models.IntegerChoices):
    VERY_BAD = 1, _("Very bad")
    BAD = 2, _("Bad")
    AVERAGE = 3, _("Average")
    GOOD = 4, _("Good")
    VERY_GOOD = 5, _("Very good")


class DeviceTypeTargetModel(models.TextChoices):
    BARRIER = "barrier", _("Barrier")
    ROAD_MARKING = "road_marking", _("Road marking")
    SIGNPOST = "signpost", _("Signpost")
    TRAFFIC_LIGHT = "traffic_light", _("Traffic light")
    TRAFFIC_SIGN = "traffic_sign", _("Traffic sign")
    ADDITIONAL_SIGN = "additional_sign", _("Additional sign")
    OTHER = "other", _("Other")


class InstallationStatus(models.TextChoices):
    IN_USE = "IN_USE", _("In use")
    COVERED = "COVERED", _("Covered")
    FALLEN = "FALLEN", _("Fallen")
    MISSING = "MISSING", _("Missing")
    OTHER = "OTHER", _("Other")


class LaneNumber(models.TextChoices):
    MAIN_1 = "1", _("Main lane")
    ADDITIONAL_LEFT_1 = "2", _("First left additional lane")
    ADDITIONAL_RIGHT_1 = "3", _("First right additional lane")
    ADDITIONAL_LEFT_2 = "4", _("Second left additional lane")
    ADDITIONAL_RIGHT_2 = "5", _("Second right additional lane")
    ADDITIONAL_LEFT_3 = "6", _("Third left additional lane")
    ADDITIONAL_RIGHT_3 = "7", _("Third right additional lane")
    ADDITIONAL_LEFT_4 = "8", _("Fourth left additional lane")
    ADDITIONAL_RIGHT_4 = "9", _("Fourth right additional lane")


class LaneType(models.TextChoices):
    MAIN = 1, _("Main lane")
    FAST = 2, _("Fast lane")
    TURN_RIGHT = 3, _("Turn right lane")
    TURN_LEFT = 4, _("Turn left lane")
    AUXILIARY = 5, _("Auxiliary straight lane")
    MERGE = 6, _("Merge lane")
    EXIT = 7, _("Exit lane")
    WEAVE = 8, _("Weaving lane")
    PUBLIC = 9, _("Public transport lane / taxi lane")
    HEAVY = 10, _("Heavy vehicle lane")
    REVERSIBLE = 11, _("Reversible lane")
    LIGHT = 20, _("Pedestrian and bike lane")
    PEDESTRIAN = 21, _("Pedestrian lane")
    BIKE = 22, _("Bike lane")


class Lifecycle(models.IntegerChoices):
    ACTIVE = 3, _("Active")
    TEMPORARILY_ACTIVE = 4, _("Temporarily active")
    TEMPORARILY_INACTIVE = 5, _("Temporarily inactive")
    INACTIVE = 6, _("Inactive")


class Reflection(models.TextChoices):
    R1 = "R1", _("r1")
    R2 = "R2", _("r2")
    R3 = "R3", _("r3")


class Size(models.TextChoices):
    SMALL = "S", _("Small")
    MEDIUM = "M", _("Medium")
    LARGE = "L", _("Large")


class Surface(models.TextChoices):
    CONVEX = "CONVEX", _("Convex")
    FLAT = "FLAT", _("Flat")


class TrafficControlDeviceTypeType(models.TextChoices):
    # road marking types
    LONGITUDINAL = "longitudinal", _("Longitudinal")
    TRANSVERSE = "transverse", _("Transverse")
    OTHER = "other", _("Other road marking")


class OrganizationLevel(models.IntegerChoices):
    """Responsible Entity Organization levels"""

    DIVISION = 10, _("division")
    SERVICE = 20, _("service")
    UNIT = 30, _("unit")
    PROJECT = 50, _("project")
