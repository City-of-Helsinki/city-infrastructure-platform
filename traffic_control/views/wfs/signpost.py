from copy import deepcopy

from gisserver.features import FeatureField, FeatureType

from traffic_control.models import SignpostReal
from traffic_control.services.common import get_lifecycle_and_validity_period_queryset
from traffic_control.services.signpost import signpost_plan_get_current
from traffic_control.views.wfs.common import (
    DEFAULT_CRS,
    DEVICE_TYPE_FIELDS,
    OTHER_CRS,
    OWNED_DEVICE_MODEL_FIELDS,
    REPLACEABLE_MODEL_FIELDS,
    SOURCE_CONTROLLED_MODEL_FIELDS,
    USER_CONTROLLED_MODEL_FIELDS,
)
from traffic_control.views.wfs.utils import EnumIntegerNameXsdElement, EnumNameXsdElement

_base_fields = (
    [
        FeatureField("id", abstract="ID of the Signpost."),
        FeatureField("location", abstract="Signpost's location (point) in EPSG:3879 coordinates."),
        FeatureField("road_name", abstract="Name of the road this signpost is installed on."),
        FeatureField("lane_number", abstract="Which lane does this signpost affect."),
        FeatureField("lane_type", abstract="The type of lane this signpost affects."),
        FeatureField("direction", abstract="Direction of the signpost. North=0, East=90, South=180 and West=270."),
        FeatureField("height", abstract="Signpost's height measured from the ground in centimeters."),
        FeatureField(
            "mount_type_description_fi",
            model_attribute="mount_type.description_fi",
            abstract="Mount type description.",
        ),
        FeatureField("value", abstract="Numeric value on the signpost."),
        FeatureField("size", xsd_class=EnumNameXsdElement, abstract="Size of the signpost."),
        FeatureField("txt", abstract="Text on the signpost."),
        FeatureField("reflection_class", xsd_class=EnumNameXsdElement, abstract="The signpost's reflection class."),
        FeatureField("attachment_class", abstract="The attachment class of the sign (e.g. P1, P2, P3)."),
        FeatureField("target_id", abstract="ID of the target the signpost is guiding to."),
        FeatureField("target_txt", abstract="Free-form text description of the target the signpost is guiding to."),
        FeatureField("electric_maintainer", abstract="Organization in charge of electric maintenance."),
        FeatureField(
            "validity_period_start",
            abstract="Starting date for period that the signpost is temporarily valid/invalid.",
        ),
        FeatureField(
            "validity_period_end",
            abstract="Ending date for period that the signpost is temporarily valid/invalid.",
        ),
        FeatureField(
            "seasonal_validity_period_information",
            abstract="Additional signpost validity period information.",
        ),
        FeatureField(
            "location_specifier",
            xsd_class=EnumIntegerNameXsdElement,
            abstract="Specifies where the signpost is in relation to the road.",
        ),
        FeatureField("double_sided", abstract="Indicates if this signpost is double sided."),
    ]
    + deepcopy(DEVICE_TYPE_FIELDS)
    + deepcopy(SOURCE_CONTROLLED_MODEL_FIELDS)
    + deepcopy(USER_CONTROLLED_MODEL_FIELDS)
    + deepcopy(OWNED_DEVICE_MODEL_FIELDS)
)

SignpostRealFeatureType = FeatureType(
    crs=DEFAULT_CRS,
    other_crs=OTHER_CRS,
    queryset=get_lifecycle_and_validity_period_queryset(SignpostReal.objects.active()).select_related("device_type"),
    fields=deepcopy(_base_fields)
    + [
        FeatureField("material", abstract="Material that the signpost is made of."),
        FeatureField("organization", abstract="Organization that installed the signpost."),
        FeatureField("manufacturer", abstract="Manufacturer of the signpost."),
        FeatureField("scanned_at", abstract="Date and time on which this signpost was last scanned."),
        FeatureField("attachment_url", abstract="URL of the attachment associated with this signpost."),
        FeatureField("installation_date", abstract="Date that the signpost was installed on."),
        FeatureField("installation_status", abstract="Installation status of the signpost."),
        FeatureField("condition", xsd_class=EnumIntegerNameXsdElement, abstract="Condition of the signpost."),
        FeatureField(
            "device_plan_id",
            model_attribute="signpost_plan",
            abstract="ID of this Signpost's plan.",
        ),
        FeatureField("mount_real_id", model_attribute="mount_real", abstract="Mount Real ID."),
        FeatureField("parent_id", model_attribute="parent", abstract="ID of the parent Signpost Real."),
    ],
)

SignpostPlanFeatureType = FeatureType(
    crs=DEFAULT_CRS,
    other_crs=OTHER_CRS,
    queryset=get_lifecycle_and_validity_period_queryset(signpost_plan_get_current()).select_related("device_type"),
    fields=deepcopy(_base_fields)
    + [
        FeatureField("plan_id", abstract="ID of the Plan that this Signpost Plan belongs to."),
        FeatureField("mount_plan_id", abstract="ID of the Mount Plan this Signpost Plan belongs to."),
        FeatureField("parent_id", model_attribute="parent", abstract="ID of the parent Signpost Plan."),
    ]
    + deepcopy(REPLACEABLE_MODEL_FIELDS),
)
