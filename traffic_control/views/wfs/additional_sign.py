from copy import deepcopy

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from gisserver.features import FeatureType
from gisserver.geometries import CRS

from traffic_control.enums import Lifecycle
from traffic_control.models import AdditionalSignPlan, AdditionalSignReal
from traffic_control.views.wfs.common import DescribedFeatureField

RD_NEW = CRS.from_srid(settings.SRID)

_base_fields = [
    DescribedFeatureField("id", description="ID of the Additional Sign."),
    DescribedFeatureField(
        "owner_name_fi",
        model_attribute="owner.name_fi",
        description="Entity that's responsible for ordering and maintenance of this sign.",
    ),
    DescribedFeatureField("location", description="Additional sign's location (point) in EPSG:3879 coordinates."),
    DescribedFeatureField(
        "device_type_code",
        model_attribute="device_type.code",
        description="Device type code.",
    ),
    DescribedFeatureField(
        "device_type_description",
        model_attribute="device_type.description",
        description="Device type description.",
    ),
    DescribedFeatureField(
        "order",
        description="Order of the additional sign that are in the same point. "
        "From top to bottom, left to right, starting from 1.",
    ),
    DescribedFeatureField("content_s", description="Structured content of the additional sign."),
    DescribedFeatureField("road_name", description="Name of the road this sign is installed on."),
    DescribedFeatureField("lane_number", description="Which lane does this sign affect."),
    DescribedFeatureField("lane_type", description="The type of lane this sign affects."),
    DescribedFeatureField("direction", description="Direction of the sign. North=0, East=90, South=180 and West=270."),
    DescribedFeatureField("height", description="Sign's height measured from the top in centimeters."),
    DescribedFeatureField("color", description="Color of the additional sign."),
    DescribedFeatureField(
        "mount_type_description_fi",
        model_attribute="mount_type.description_fi",
        description="Mount type description.",
    ),
    DescribedFeatureField("reflection_class", description="The sign's reflection class."),
    DescribedFeatureField("surface_class", description="The sign's surface class."),
    DescribedFeatureField(
        "validity_period_start",
        description="Starting date for period that the sign is temporarily valid/invalid.",
    ),
    DescribedFeatureField(
        "validity_period_end",
        description="Ending date for period that the sign is temporarily valid/invalid.",
    ),
    DescribedFeatureField(
        "seasonal_validity_period_start",
        description="Starting date for period that the sign is valid/invalid",
    ),
    DescribedFeatureField(
        "seasonal_validity_period_end",
        description="Ending date for period that the sign is temporarily valid/invalid",
    ),
]

AdditionalSignRealFeatureType = FeatureType(
    queryset=AdditionalSignReal.objects.active()
    .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
    .filter(
        Q(validity_period_start__isnull=True)
        | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
    ),
    fields=deepcopy(_base_fields)
    + [
        DescribedFeatureField("manufacturer", description="Manufacturer of the sign."),
        DescribedFeatureField("legacy_code", description="Legacy code of the additional sign type"),
        DescribedFeatureField("permit_decision_id", description="Permit Decision ID"),
        DescribedFeatureField("attachment_url", description="URL for additional material bout the signpost."),
        DescribedFeatureField("installation_id", description="Installation ID"),
        DescribedFeatureField("installation_details", description="Additional details about the installation."),
        DescribedFeatureField("installation_date", description="Date that the sign was installed on."),
        DescribedFeatureField("installation_status", description="Installation status of the sign."),
        DescribedFeatureField("condition", description="Condition of the signpost"),
        DescribedFeatureField(
            "device_plan_id",
            model_attribute="additional_sign_plan",
            description="ID of this Additional Sign's plan.",
        ),
    ],
    other_crs=[RD_NEW],
)

AdditionalSignPlanFeatureType = FeatureType(
    queryset=AdditionalSignPlan.objects.active()
    .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
    .filter(
        Q(validity_period_start__isnull=True)
        | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
    ),
    fields=deepcopy(_base_fields)
    + [
        DescribedFeatureField("plan_id", description="ID of the Plan that this Additional Sign belongs to."),
    ],
    other_crs=[RD_NEW],
)
