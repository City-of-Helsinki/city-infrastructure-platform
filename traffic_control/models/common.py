import uuid
from typing import Optional

from auditlog.registry import auditlog
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import Enum, EnumField


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


class LaneType(Enum):
    MAIN = 1
    FAST = 2
    TURN_RIGHT = 3
    TURN_LEFT = 4
    AUXILIARY = 5
    MERGE = 6
    EXIT = 7
    WEAVE = 8
    PUBLIC = 9
    HEAVY = 10
    REVERSIBLE = 11
    LIGHT = 20
    PEDESTRIAN = 21
    BIKE = 22

    class Labels:
        MAIN = _("Main lane")
        FAST = _("Fast lane")
        TURN_RIGHT = _("Turn right lane")
        TURN_LEFT = _("Turn left lane")
        AUXILIARY = _("Auxiliary straight lane")
        MERGE = _("Merge lane")
        EXIT = _("Exit lane")
        WEAVE = _("Weaving lane")
        PUBLIC = _("Public transport lane / taxi lane")
        HEAVY = _("Heavy vehicle lane")
        REVERSIBLE = _("Reversible lane")
        LIGHT = _("Pedestrian and bike lane")
        PEDESTRIAN = _("Pedestrian lane")
        BIKE = _("Bike lane")


class LaneNumber(Enum):
    MAIN_1 = "11"
    MAIN_2 = "21"
    REVERSIBLE = "31"
    ADDITIONAL_LEFT_1 = "X2"
    ADDITIONAL_RIGHT_1 = "X3"
    ADDITIONAL_LEFT_2 = "X4"
    ADDITIONAL_RIGHT_2 = "X5"
    ADDITIONAL_LEFT_3 = "X6"
    ADDITIONAL_RIGHT_3 = "X7"
    ADDITIONAL_LEFT_4 = "X8"
    ADDITIONAL_RIGHT_4 = "X9"

    class Labels:
        MAIN_1 = _("Main lane")
        MAIN_2 = _("Main lane")
        REVERSIBLE = _("Lane allowing traffic to both directions")
        ADDITIONAL_LEFT_1 = _("First left additional lane")
        ADDITIONAL_RIGHT_1 = _("First right additional lane")
        ADDITIONAL_LEFT_2 = _("Second left additional lane")
        ADDITIONAL_RIGHT_2 = _("Second right additional lane")
        ADDITIONAL_LEFT_3 = _("Third left additional lane")
        ADDITIONAL_RIGHT_3 = _("Third right additional lane")
        ADDITIONAL_LEFT_4 = _("Fourth left additional lane")
        ADDITIONAL_RIGHT_4 = _("Fourth right additional lane")


class DeviceTypeTargetModel(Enum):
    BARRIER = "barrier"
    ROAD_MARKING = "road_marking"
    SIGNPOST = "signpost"
    TRAFFIC_LIGHT = "traffic_light"
    TRAFFIC_SIGN = "traffic_sign"

    class Labels:
        BARRIER = _("Barrier")
        ROAD_MARKING = _("Road marking")
        SIGNPOST = _("Signpost")
        TRAFFIC_LIGHT = _("Traffic light")
        TRAFFIC_SIGN = _("Traffic sign")


class TrafficControlDeviceTypeType(Enum):
    # road marking types
    LONGITUDINAL = "longitudinal"
    TRANSVERSE = "transverse"
    OTHER = "other"

    class Labels:
        LONGITUDINAL = _("Longitudinal")
        TRANSVERSE = _("Transverse")
        OTHER = _("Other road marking")


class TrafficControlDeviceTypeQuerySet(models.QuerySet):
    def for_target_model(self, target_model: DeviceTypeTargetModel):
        return self.filter(Q(target_model=None) | Q(target_model=target_model))


class TrafficControlDeviceType(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    code = models.CharField(_("Code"), unique=True, max_length=32)
    description = models.CharField(
        _("Description"), max_length=254, blank=True, null=True
    )
    legacy_code = models.CharField(
        _("Legacy code"), max_length=32, blank=True, null=True
    )
    legacy_description = models.CharField(
        _("Legacy description"), max_length=254, blank=True, null=True
    )
    target_model = EnumField(
        DeviceTypeTargetModel,
        verbose_name=_("Target data model"),
        max_length=32,
        blank=True,
        null=True,
    )
    type = EnumField(
        TrafficControlDeviceTypeType,
        verbose_name=_("Type"),
        max_length=50,
        blank=True,
        null=True,
    )

    objects = TrafficControlDeviceTypeQuerySet.as_manager()

    class Meta:
        db_table = "traffic_control_device_type"
        verbose_name = _("Traffic Control Device Type")
        verbose_name_plural = _("Traffic Control Device Types")

    def __str__(self):
        return "%s - %s" % (self.code, self.description)

    def save(self, *args, **kwargs):
        if self.pk:
            self.validate_change_target_model(self.target_model, raise_exception=True)

        super().save(*args, **kwargs)

    def _has_invalid_related_models(self, target_type: DeviceTypeTargetModel) -> bool:
        """
        Check if instance has related models that are invalid with given target
        type value.
        """
        relations = [
            "barrierplan",
            "barrierreal",
            "roadmarkingplan",
            "roadmarkingreal",
            "signpostplan",
            "signpostreal",
            "trafficlightplan",
            "trafficlightreal",
            "trafficsignplan",
            "trafficsignreal",
        ]
        ignore_prefix = target_type.value.replace("_", "")
        relevant_relations = [
            relation for relation in relations if not relation.startswith(ignore_prefix)
        ]

        related_pks = []
        queryset = TrafficControlDeviceType.objects.filter(pk=self.pk).values_list(
            *relevant_relations
        )
        if queryset.exists():
            related_pks = queryset.first()

        return any(related_pks)

    def validate_change_target_model(
        self,
        new_target_type: Optional[DeviceTypeTargetModel],
        raise_exception: bool = False,
    ) -> bool:
        """
        Validate if instance target_model value can be changed to the given new_value.

        Validate that relations on other models do not become non-allowed after changing
        instance target_model to the new value.

        Returns boolean value indicating if change is valid or raises ValidationError if
        raise_exception is True
        """
        if not new_target_type:
            return True  # None is always valid value

        has_invalid_relations = self._has_invalid_related_models(new_target_type)

        if raise_exception and has_invalid_relations:
            raise ValidationError(
                f"Some traffic control devices related to this device type instance "
                f"will become invalid if target_model value is changed to "
                f"{new_target_type.value}. target_model can not be changed until this "
                f"is resolved."
            )

        return True

    def validate_relation(self, model: DeviceTypeTargetModel):
        """
        Validate that the related model is allowed to have relationship
        to this TrafficControlDeviceType instance.
        """
        if self.target_model and self.target_model is not model:
            return False

        return True


auditlog.register(TrafficControlDeviceType)
