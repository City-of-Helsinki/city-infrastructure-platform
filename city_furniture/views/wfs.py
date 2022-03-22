from copy import deepcopy
from typing import Optional, Type

from django.conf import settings
from django.db.models import Q
from enumfields import Enum
from gisserver import output
from gisserver.features import ComplexFeatureField, FeatureField, FeatureType, ServiceDescription
from gisserver.geometries import CRS
from gisserver.operations import wfs20
from gisserver.operations.base import OutputFormat
from gisserver.operations.wfs20 import GetFeature
from gisserver.output import GeoJsonRenderer
from gisserver.types import XsdElement
from gisserver.views import WFSView

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from traffic_control.enums import Lifecycle

RD_NEW = CRS.from_srid(settings.SRID)


class CustomGeoJsonRenderer(GeoJsonRenderer):
    def _format_geojson_value(self, value):
        """Add support for formatting Enums"""
        if isinstance(value, Enum):
            return value.label
        return super()._format_geojson_value(value)


class CustomGetFeature(GetFeature):
    # Use CustomGeoJsonRenderer
    output_formats = [
        OutputFormat("application/gml+xml", version="3.2", renderer_class=output.gml32_renderer, title="GML"),
        OutputFormat("text/xml", subtype="gml/3.2.1", renderer_class=output.gml32_renderer, title="GML 3.2.1"),
        OutputFormat(
            "application/json",
            subtype="geojson",
            charset="utf-8",
            renderer_class=CustomGeoJsonRenderer,
            title="GeoJSON",
        ),
        OutputFormat("text/csv", subtype="csv", charset="utf-8", renderer_class=output.csv_renderer, title="CSV"),
    ]


class DescribedFeatureField(FeatureField):
    """FeatureField with an added description attribute"""

    def __init__(
        self,
        name,
        model_attribute=None,
        model=None,
        parent: "Optional[ComplexFeatureField]" = None,
        abstract=None,
        xsd_class: Optional[Type[XsdElement]] = None,
        description: str = "",
    ):
        self.description = description
        super().__init__(name, model_attribute, model, parent, abstract, xsd_class)


class CityFurnitureWFSView(WFSView):
    service_description = ServiceDescription(title="City Furniture")
    index_template_name = "wfs/index.html"

    accept_operations = {
        "WFS": {
            "GetCapabilities": wfs20.GetCapabilities,
            "DescribeFeatureType": wfs20.DescribeFeatureType,
            "GetFeature": CustomGetFeature,
            "GetPropertyValue": wfs20.GetPropertyValue,
            "ListStoredQueries": wfs20.ListStoredQueries,
            "DescribeStoredQueries": wfs20.DescribeStoredQueries,
        }
    }

    furniture_signpost_base_fields = [
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
        DescribedFeatureField(
            "location_additional_info", description="Additional information about the install location."
        ),
        DescribedFeatureField(
            "direction",
            description="The direction, in which a person is standing when looking directly at the signpost.",
        ),
        DescribedFeatureField(
            "device_type_code", model_attribute="device_type.code", description="Device type description."
        ),
        DescribedFeatureField(
            "device_type_description",
            model_attribute="device_type.description",
            description="Device type description.",
        ),
        DescribedFeatureField(
            "color_code", model_attribute="color.rgb", description="Signpost color in rgb hex format."
        ),
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
        DescribedFeatureField(
            "size", description="Size of the signpost. Filled only if signpost is of non-standard size."
        ),
        DescribedFeatureField("arrow_direction", description="Direction of the arrow on the signpost."),
        DescribedFeatureField(
            "target_name_fi",
            model_attribute="target.name_fi",
            description="Name of the target entity related to this signpost.",
        ),
        DescribedFeatureField(
            "content_responsible_entity", description="Entity responsible for this signpost's content."
        ),
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

    feature_types = [
        FeatureType(
            FurnitureSignpostReal.objects.active().filter(
                Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE)
            ),
            fields=deepcopy(furniture_signpost_base_fields)
            + [
                DescribedFeatureField("installation_date", description="Date that the signpost was installed on."),
                DescribedFeatureField("condition", description="Condition of the signpost"),
            ],
            other_crs=[RD_NEW],
        ),
        FeatureType(
            FurnitureSignpostPlan.objects.active().filter(
                Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE)
            ),
            fields=deepcopy(furniture_signpost_base_fields)
            + [
                DescribedFeatureField("plan_id", description="ID of the Plan that this signpost belongs to."),
            ],
            other_crs=[RD_NEW],
        ),
    ]
