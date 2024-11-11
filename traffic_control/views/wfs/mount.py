from copy import deepcopy

from django.db.models import Q
from django.utils import timezone
from gisserver.features import FeatureField, FeatureType, field

from traffic_control.enums import Lifecycle
from traffic_control.models import MountReal
from traffic_control.services.mount import mount_plan_get_current
from traffic_control.views.wfs.common import DEFAULT_CRS, OTHER_CRS

_base_fields = [
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
        model_attribute="location_specifier",
        abstract="Specifies where the mount is in relation to the road.",
    ),
    FeatureField("source_name", abstract="Name of the source of this mount."),
    FeatureField("source_id", abstract="ID of this mount in the source."),
    FeatureField("created_at", abstract="Date when this mount was created."),
    FeatureField("created_by", abstract="User who created this mount."),
    FeatureField("updated_at", abstract="Date when this mount was last updated."),
    FeatureField("updated_by", abstract="User who last updated this mount."),
    FeatureField("owner_name_fi", model_attribute="owner.name_fi", abstract="Name of the owner of the mount."),
    FeatureField(
        "responsible_entity", model_attribute="responsible_entity.name", abstract="Name of the responsile of the mount."
    ),
    FeatureField("lifecycle", abstract="Lifecycle of the mount."),
]


MountRealFeatureType = FeatureType(
    crs=DEFAULT_CRS,
    other_crs=OTHER_CRS,
    queryset=MountReal.objects.active().filter(
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
        FeatureField(
            "replaced_by",
            model_attribute="replacement_to_new.new",
            abstract="ID of the mount plan which replaces this mount plan",
        ),
        FeatureField(
            "replaces",
            model_attribute="replacement_to_old.old",
            abstract="ID of the mount plan which this mount plan replaces",
        ),
    ],
)
