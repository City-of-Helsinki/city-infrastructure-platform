from copy import deepcopy

from django.db.models import Q
from django.utils import timezone
from gisserver.features import FeatureField, FeatureType, field

from traffic_control.enums import Lifecycle
from traffic_control.models import MountReal
from traffic_control.services.mount import mount_plan_get_current
from traffic_control.views.wfs.common import (
    DEFAULT_CRS,
    OTHER_CRS,
    OWNED_DEVICE_MODEL_FIELDS,
    REPLACEABLE_MODEL_FIELDS,
    SOURCE_CONTROLLED_MODEL_FIELDS,
    USER_CONTROLLED_MODEL_FIELDS,
)
from traffic_control.views.wfs.utils import EnumNameXsdElement

_base_fields = (
    [
        FeatureField("id", abstract="ID of the Mount."),
        FeatureField("location", abstract="Location of the Mount."),
        FeatureField("height", abstract="Height of the Mount."),
        FeatureField(
            "mount_type_description_fi", model_attribute="mount_type.description_fi", abstract="Mount type description."
        ),
        FeatureField("base", abstract="Base of the Mount."),
        field("portal_type", fields=["structure", "build_type", "model"], abstract="Portal type for the mount."),
        FeatureField("material", abstract="Material of the Mount."),
        FeatureField("validity_period_start", abstract="Date on which this mount becomes active."),
        FeatureField("validity_period_end", abstract="Date after which this mount becomes inactive."),
        FeatureField("txt", abstract="Text written on the mount."),
        FeatureField("electric_accountable", abstract="The entity responsible for the mount (if electric)."),
        FeatureField("is_foldable", abstract="Is the mount foldable"),
        FeatureField("cross_bar_length", abstract="Length of the cross bar for this mount in centimeters."),
        FeatureField("road_name", abstract="Name of the road this mount is installed at."),
        FeatureField(
            "location_specifier",
            xsd_class=EnumNameXsdElement,
            abstract="Specifies where the mount is in relation to the road.",
        ),
    ]
    + deepcopy(SOURCE_CONTROLLED_MODEL_FIELDS)
    + deepcopy(USER_CONTROLLED_MODEL_FIELDS)
    + deepcopy(OWNED_DEVICE_MODEL_FIELDS)
)


MountRealFeatureType = FeatureType(
    crs=DEFAULT_CRS,
    other_crs=OTHER_CRS,
    queryset=MountReal.objects.active()
    .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
    .filter(
        Q(validity_period_start__isnull=True)
        | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
    ),
    fields=deepcopy(_base_fields)
    + [
        FeatureField(
            "mount_plan_id", model_attribute="mount_plan.id", abstract="ID of the Mount plan related to this Mount"
        ),
        FeatureField("inspected_at", abstract="Timestamp when the mount was inspected."),
        FeatureField("diameter", abstract="Diameter of the mount."),
        FeatureField("scanned_at", abstract="Timestamp when the mount was scanned."),
        FeatureField("attachment_url", abstract="URL of the attachment of the mount."),
    ],
)


MountPlanFeatureType = FeatureType(
    crs=DEFAULT_CRS,
    other_crs=OTHER_CRS,
    queryset=mount_plan_get_current()
    .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
    .filter(
        Q(validity_period_start__isnull=True)
        | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
    ),
    fields=deepcopy(_base_fields)
    + [
        FeatureField("plan_id", model_attribute="plan.id", abstract="ID of the plan related to this MountPlan"),
    ]
    + deepcopy(REPLACEABLE_MODEL_FIELDS),
)
