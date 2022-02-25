from copy import deepcopy

from django.conf import settings
from django.db.models import Q
from enumfields import Enum
from gisserver import output
from gisserver.features import FeatureType, field, ServiceDescription
from gisserver.geometries import CRS
from gisserver.operations import wfs20
from gisserver.operations.base import OutputFormat
from gisserver.operations.wfs20 import GetFeature
from gisserver.output import GeoJsonRenderer
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


class CityFurnitureWFSView(WFSView):
    service_description = ServiceDescription(title="City Furniture")
    xml_namespace = "http://example.org/gisserver"

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
        "id",
        "source_name",
        "source_id",
        "project_id",
        field("owner_name_fi", model_attribute="owner.name_fi"),
        field("responsible_entity_name", model_attribute="responsible_entity.name"),
        "location",
        "location_name",
        "location_additional_info",
        "direction",
        field("device_type_code", model_attribute="device_type.code"),
        field("color_name", model_attribute="color.name"),
        "height",
        field("mount_type_description_fi", model_attribute="mount_type.description_fi"),
        field("parent_id", model_attribute="parent.id"),
        "order",
        "pictogram",
        "value",
        "size",
        "arrow_direction",
        field("target_name_fi", model_attribute="target.name_fi"),
        "content_responsible_entity",
        "text_content_fi",
        "text_content_sw",
        "text_content_en",
        "validity_period_end",
        "validity_period_start",
        "additional_material_url",
        "lifecycle",
    ]

    feature_types = [
        FeatureType(
            FurnitureSignpostReal.objects.active().filter(
                Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE)
            ),
            fields=deepcopy(furniture_signpost_base_fields)
            + [
                "installation_date",
                "installation_status",
                "condition",
            ],
            other_crs=[RD_NEW],
        ),
        FeatureType(
            FurnitureSignpostPlan.objects.active().filter(
                Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE)
            ),
            fields=deepcopy(furniture_signpost_base_fields)
            + [
                "plan",
            ],
            other_crs=[RD_NEW],
        ),
    ]
