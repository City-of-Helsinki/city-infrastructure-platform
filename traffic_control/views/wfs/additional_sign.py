from copy import deepcopy

from django.db.models import Q
from django.utils import timezone
from gisserver.features import FeatureField, FeatureType

from traffic_control.enums import Lifecycle
from traffic_control.models import AdditionalSignReal
from traffic_control.services.additional_sign import additional_sign_plan_get_current
from traffic_control.views.wfs.common import (
    DEFAULT_CRS,
    DEVICE_TYPE_FIELDS,
    EnumNameXsdElement,
    OTHER_CRS,
    OWNED_DEVICE_MODEL_FIELDS,
    REPLACEABLE_MODEL_FIELDS,
    SOURCE_CONTROLLED_MODEL_FIELDS,
    USER_CONTROLLED_MODEL_FIELDS,
)

_base_fields = (
    [
        FeatureField("id", abstract="ID of the Additional Sign."),
        FeatureField("location", abstract="Additional sign's location (point) in EPSG:3879 coordinates."),
        FeatureField(
            "order",
            abstract="Order of the additional sign that are in the same point. "
            "From top to bottom, left to right, starting from 1.",
        ),
        FeatureField("content_s", abstract="Structured content of the additional sign."),
        FeatureField("road_name", abstract="Name of the road this sign is installed on."),
        FeatureField("lane_number", abstract="Which lane does this sign affect."),
        FeatureField("lane_type", abstract="The type of lane this sign affects."),
        FeatureField("direction", abstract="Direction of the sign. North=0, East=90, South=180 and West=270."),
        FeatureField("size", xsd_class=EnumNameXsdElement, abstract="Size of the additional sign."),
        FeatureField("height", abstract="Sign's height measured from the top in centimeters."),
        FeatureField("color", xsd_class=EnumNameXsdElement, abstract="Color of the additional sign."),
        FeatureField(
            "mount_type_description_fi",
            model_attribute="mount_type.description_fi",
            abstract="Mount type description.",
        ),
        FeatureField("reflection_class", xsd_class=EnumNameXsdElement, abstract="The sign's reflection class."),
        FeatureField("surface_class", xsd_class=EnumNameXsdElement, abstract="The sign's surface class."),
        FeatureField(
            "validity_period_start",
            abstract="Starting date for period that the sign is temporarily valid/invalid.",
        ),
        FeatureField(
            "validity_period_end",
            abstract="Ending date for period that the sign is temporarily valid/invalid.",
        ),
        FeatureField(
            "seasonal_validity_period_information",
            abstract="Additional sign's validity period information.",
        ),
        FeatureField(
            "parent_id",
            model_attribute="parent.id",
            abstract="Parent ID of the sign",
        ),
        FeatureField(
            "additional_information",
            abstract="Additional information about the sign",
        ),
        FeatureField(
            "location_specifier",
            xsd_class=EnumNameXsdElement,
            abstract="Specifies where the mount is in relation to the road.",
        ),
    ]
    + deepcopy(DEVICE_TYPE_FIELDS)
    + deepcopy(SOURCE_CONTROLLED_MODEL_FIELDS)
    + deepcopy(USER_CONTROLLED_MODEL_FIELDS)
    + deepcopy(OWNED_DEVICE_MODEL_FIELDS)
)

AdditionalSignRealFeatureType = FeatureType(
    crs=DEFAULT_CRS,
    other_crs=OTHER_CRS,
    queryset=AdditionalSignReal.objects.active()
    .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
    .filter(
        Q(validity_period_start__isnull=True)
        | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
    ),
    fields=deepcopy(_base_fields)
    + [
        FeatureField("manufacturer", abstract="Manufacturer of the sign."),
        FeatureField("legacy_code", abstract="Legacy code of the additional sign type"),
        FeatureField("permit_decision_id", abstract="Permit Decision ID"),
        FeatureField("attachment_url", abstract="URL for additional material bout the signpost."),
        FeatureField("installation_id", abstract="Installation ID"),
        FeatureField("installation_details", abstract="Additional details about the installation."),
        FeatureField("installation_date", abstract="Date that the sign was installed on."),
        FeatureField("installation_status", abstract="Installation status of the sign."),
        FeatureField("condition", xsd_class=EnumNameXsdElement, abstract="Condition of the signpost"),
        FeatureField(
            "device_plan_id",
            model_attribute="additional_sign_plan",
            abstract="ID of this Additional Sign's plan.",
        ),
        FeatureField("mount_real_id", model_attribute="mount_real", abstract="Mount Real ID"),
    ],
)

AdditionalSignPlanFeatureType = FeatureType(
    crs=DEFAULT_CRS,
    other_crs=OTHER_CRS,
    queryset=additional_sign_plan_get_current()
    .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
    .filter(
        Q(validity_period_start__isnull=True)
        | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
    ),
    fields=deepcopy(_base_fields)
    + [
        FeatureField("plan_id", abstract="ID of the Plan that this Additional Sign Plan belongs to."),
        FeatureField("mount_plan_id", abstract="ID of the Mount Plan that this Additional Sign plan belongs to."),
    ]
    + deepcopy(REPLACEABLE_MODEL_FIELDS),
)
