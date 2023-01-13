from typing import Optional, Type

from enumfields import Enum
from gisserver import output
from gisserver.features import ComplexFeatureField, FeatureField
from gisserver.operations.base import OutputFormat
from gisserver.operations.wfs20 import GetFeature
from gisserver.output import GeoJsonRenderer
from gisserver.types import XsdElement

from .utils import YXGML32Renderer


class CustomGeoJsonRenderer(GeoJsonRenderer):
    def _format_geojson_value(self, value):
        """Add support for formatting Enums"""
        if isinstance(value, Enum):
            return value.label
        return super()._format_geojson_value(value)


class CustomGetFeature(GetFeature):
    # Use CustomGeoJsonRenderer
    output_formats = [
        OutputFormat("application/gml+xml", version="3.2", renderer_class=YXGML32Renderer, title="GML"),
        OutputFormat("text/xml", subtype="gml/3.2.1", renderer_class=YXGML32Renderer, title="GML 3.2.1"),
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
