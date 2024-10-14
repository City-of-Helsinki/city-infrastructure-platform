from copy import deepcopy

from django.db.models import Q
from django.utils import timezone
from gisserver.features import FeatureField, FeatureType

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from traffic_control.enums import Lifecycle
from traffic_control.views.wfs.common import DEFAULT_CRS, OTHER_CRS

_base_fields = [
    FeatureField("id", abstract="ID of the Furniture Signpost."),
    FeatureField(
        "owner_name_fi",
        model_attribute="owner.name_fi",
        abstract="Entity that's responsible for ordering and maintenance of this signpost.",
    ),
    FeatureField(
        "responsible_entity_name",
        model_attribute="responsible_entity.name",
        abstract="Entity who is responsible for this signpost.",
    ),
    FeatureField("location", abstract="Signpost's location (point) in EPSG:3879 coordinates."),
    FeatureField(
        "location_name_fi",
        abstract="Verbose name for the signpost's location, e.g. street, park or island in Finnish.",
    ),
    FeatureField(
        "location_name_sw",
        abstract="Verbose name for the signpost's location, e.g. street, park or island in Swedish.",
    ),
    FeatureField(
        "location_name_en",
        abstract="Verbose name for the signpost's location, e.g. street, park or island in English.",
    ),
    FeatureField("location_additional_info", abstract="Additional information about the install location."),
    FeatureField(
        "direction",
        abstract="The direction, in which a person is standing when looking directly at the signpost."
        "e.g. when looking directly north, the direction should be 0, East=90, South=180 and West=270.",
    ),
    FeatureField("device_type_code", model_attribute="device_type.code", abstract="Device type code."),
    FeatureField(
        "device_type_description",
        model_attribute="device_type.description_fi",
        abstract="Device type description.",
    ),
    FeatureField("color_code", model_attribute="color.rgb", abstract="Signpost color in rgb hex format."),
    FeatureField("height", abstract="Signpost height measured from the top in centimeters."),
    FeatureField(
        "mount_type_description_fi",
        model_attribute="mount_type.description_fi",
        abstract="Mount type description.",
    ),
    FeatureField(
        "parent_id",
        model_attribute="parent.id",
        abstract="ID of the Parent signpost that this signpost is inside of.",
    ),
    FeatureField(
        "order",
        abstract="Order of the signposts that are in the same point. "
        "From top to bottom, left to right, starting from 1.",
    ),
    FeatureField("pictogram", abstract="Description of the pictogram in this signpost."),
    FeatureField("value", abstract="Value in the signposts, when its numeric."),
    FeatureField("size", abstract="Size of the signpost. Filled only if signpost is of non-standard size."),
    FeatureField("arrow_direction", abstract="Direction of the arrow on the signpost."),
    FeatureField(
        "target_name_fi",
        model_attribute="target.name_fi",
        abstract="Name of the target entity related to this signpost.",
    ),
    FeatureField("content_responsible_entity", abstract="Entity responsible for this signpost's content."),
    FeatureField("text_content_fi", abstract="Text content of the signpost in Finnish"),
    FeatureField("text_content_sw", abstract="Text content of the signpost in Swedish"),
    FeatureField("text_content_en", abstract="Text content of the signpost in English"),
    FeatureField(
        "validity_period_start",
        abstract="Starting date for period that the signpost is temporarily valid/invalid.",
    ),
    FeatureField(
        "validity_period_end",
        abstract="Ending date for period that the signpost is temporarily valid/invalid.",
    ),
    FeatureField("additional_material_url", abstract="URL for additional material bout the signpost."),
]


FurnitureSignpostRealFeatureType = FeatureType(
    crs=DEFAULT_CRS,
    other_crs=OTHER_CRS,
    queryset=FurnitureSignpostReal.objects.active()
    .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
    .filter(
        Q(validity_period_start__isnull=True)
        | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
    ),
    fields=deepcopy(_base_fields)
    + [
        FeatureField("installation_date", abstract="Date that the signpost was installed on."),
        FeatureField("condition", abstract="Condition of the signpost"),
        FeatureField(
            "device_plan_id",
            model_attribute="furniture_signpost_plan",
            abstract="ID of this Signpost's plan.",
        ),
    ],
)

FurnitureSignpostPlanFeatureType = FeatureType(
    crs=DEFAULT_CRS,
    other_crs=OTHER_CRS,
    queryset=FurnitureSignpostPlan.objects.active()
    .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
    .filter(
        Q(validity_period_start__isnull=True)
        | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
    ),
    fields=deepcopy(_base_fields)
    + [
        FeatureField("plan_id", abstract="ID of the Plan that this signpost belongs to."),
    ],
)
