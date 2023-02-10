from typing import Optional, Type

from django.conf import settings
from enumfields import Enum
from gisserver.features import ComplexFeatureField, FeatureField
from gisserver.geometries import CRS
from gisserver.operations.base import OutputFormat
from gisserver.operations.wfs20 import GetFeature
from gisserver.output import GeoJsonRenderer
from gisserver.types import XsdElement

from traffic_control.views.wfs.utils import SwapBoundingBoxMixin, YXGML32Renderer

DEFAULT_CRS = CRS.from_srid(settings.SRID)

OTHER_CRS = [
    CRS.from_srid(3067),  # ETRS89 / TM35FIN(E,N)
    CRS.from_srid(4326),  # WGS84
    CRS.from_srid(3857),  # WGS84 / Pseudo-Mercator
]


class CustomGeoJsonRenderer(GeoJsonRenderer):
    def _format_geojson_value(self, value):
        """Add support for formatting Enums"""
        if isinstance(value, Enum):
            return value.label
        return super()._format_geojson_value(value)


class CustomGetFeature(SwapBoundingBoxMixin, GetFeature):
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
