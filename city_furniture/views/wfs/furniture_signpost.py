from copy import deepcopy

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from gisserver.features import FeatureType
from gisserver.geometries import CRS

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from traffic_control.enums import Lifecycle
from traffic_control.views.wfs.common import DescribedFeatureField

RD_NEW = CRS.from_srid(settings.SRID)

_base_fields = [
    DescribedFeatureField("id", description="ID of the Furniture Signpost."),
    DescribedFeatureField("project_id", description="The Project ID that this signpost belongs to in Projectwise."),
    DescribedFeatureField(
        "owner_name_fi",
        model_attribute="owner.name_fi",
        description="Entity that's responsible for ordering and mainteinance of this signpost.",
    ),
    DescribedFeatureField(
        "responsible_entity_name",
        model_attribute="responsible_entity.name",
        description="Person who is responsible for this signpost.",
    ),
    DescribedFeatureField("location", description="Signpost's location (point) in EPSG:3879 coordinates."),
    DescribedFeatureField(
        "location_name", description="Verbose name for the signpost's location, e.g. street, park or island."
    ),
    DescribedFeatureField("location_additional_info", description="Additional information about the install location."),
    DescribedFeatureField(
        "direction",
        description="The direction, in which a person is standing when looking directly at the signpost."
        "e.g. when looking directly north, the direction should be 0, East=90, South=180 and West=270.",
    ),
    DescribedFeatureField("device_type_code", model_attribute="device_type.code", description="Device type code."),
    DescribedFeatureField(
        "device_type_description",
        model_attribute="device_type.description",
        description="Device type description.",
    ),
    DescribedFeatureField("color_code", model_attribute="color.rgb", description="Signpost color in rgb hex format."),
    DescribedFeatureField("height", description="Signpost height measured from the top in centimeters."),
    DescribedFeatureField(
        "mount_type_description_fi",
        model_attribute="mount_type.description_fi",
        description="Mount type description.",
    ),
    DescribedFeatureField(
        "parent_id",
        model_attribute="parent.id",
        description="ID of the Parent signpost that this signpost is inside of.",
    ),
    DescribedFeatureField(
        "order",
        description="Order of the signposts that are in the same point. "
        "From top to bottom, left to right, starting from 1.",
    ),
    DescribedFeatureField("pictogram", description="Description of the pictogram in this signpost."),
    DescribedFeatureField("value", description="Value in the signposts, when its numeric."),
    DescribedFeatureField("size", description="Size of the signpost. Filled only if signpost is of non-standard size."),
    DescribedFeatureField("arrow_direction", description="Direction of the arrow on the signpost."),
    DescribedFeatureField(
        "target_name_fi",
        model_attribute="target.name_fi",
        description="Name of the target entity related to this signpost.",
    ),
    DescribedFeatureField("content_responsible_entity", description="Entity responsible for this signpost's content."),
    DescribedFeatureField("text_content_fi", description="Text content of the signpost in Finnish"),
    DescribedFeatureField("text_content_sw", description="Text content of the signpost in Swedish"),
    DescribedFeatureField("text_content_en", description="Text content of the signpost in English"),
    DescribedFeatureField(
        "validity_period_start",
        description="Starting date for period that the signpost is temporarily valid/invalid.",
    ),
    DescribedFeatureField(
        "validity_period_end",
        description="Ending date for period that the signpost is temporarily valid/invalid.",
    ),
    DescribedFeatureField("additional_material_url", description="URL for additional material bout the signpost."),
]

FurnitureSignpostRealFeatureType = FeatureType(
    queryset=FurnitureSignpostReal.objects.active()
    .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
    .filter(
        Q(validity_period_start__isnull=True)
        | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
    ),
    fields=deepcopy(_base_fields)
    + [
        DescribedFeatureField("installation_date", description="Date that the signpost was installed on."),
        DescribedFeatureField("condition", description="Condition of the signpost"),
        DescribedFeatureField(
            "device_plan_id",
            model_attribute="furniture_signpost_plan",
            description="ID of this Signpost's plan.",
        ),
    ],
    other_crs=[RD_NEW],
)

FurnitureSignpostPlanFeatureType = FeatureType(
    queryset=FurnitureSignpostPlan.objects.active()
    .filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))
    .filter(
        Q(validity_period_start__isnull=True)
        | (Q(validity_period_end__gte=timezone.now()) & Q(validity_period_start__lte=timezone.now()))
    ),
    fields=deepcopy(_base_fields)
    + [
        DescribedFeatureField("plan_id", description="ID of the Plan that this signpost belongs to."),
    ],
    other_crs=[RD_NEW],
)
