from typing import Optional, Type

from django.conf import settings
from django.db import models
from enumfields import Enum
from gisserver.features import ComplexFeatureField, FeatureField
from gisserver.geometries import CRS
from gisserver.operations.base import OutputFormat
from gisserver.operations.wfs20 import GetFeature
from gisserver.output import GeoJsonRenderer
from gisserver.output.utils import ChunkedQuerySetIterator
from gisserver.types import XsdElement

from traffic_control.views.wfs.utils import EnumNameXsdElement, IconXsdElement, SwapBoundingBoxMixin, YXGML32Renderer
from traffic_control.views.wfs.workarounds import replace__restore_caches

DEFAULT_CRS = CRS.from_srid(settings.SRID)

OTHER_CRS = [
    CRS.from_srid(3067),  # ETRS89 / TM35FIN(E,N)
    CRS.from_srid(4326),  # WGS84
    CRS.from_srid(3857),  # WGS84 / Pseudo-Mercator
]

SOURCE_CONTROLLED_MODEL_FIELDS = [
    FeatureField("source_name", abstract="Name of the source of this device."),
    FeatureField("source_id", abstract="ID of this device in the source."),
]

USER_CONTROLLED_MODEL_FIELDS = [
    FeatureField("created_at", abstract="Date when this device was created."),
    FeatureField("created_by", abstract="User who created this device."),
    FeatureField("updated_at", abstract="Date when this device was last updated."),
    FeatureField("updated_by", abstract="User who last updated this device."),
]

OWNED_DEVICE_MODEL_FIELDS = [
    FeatureField("owner_name_fi", model_attribute="owner.name_fi", abstract="Name of the owner of the device."),
    FeatureField("lifecycle", xsd_class=EnumNameXsdElement, abstract="Lifecycle of the device."),
]

REPLACEABLE_MODEL_FIELDS = [
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
]

DEVICE_TYPE_FIELDS = [
    FeatureField(
        "device_type_code",
        model_attribute="device_type.code",
        abstract="Device type code.",
    ),
    FeatureField(
        "device_type_description",
        model_attribute="device_type.description",
        abstract="Device type description.",
    ),
    FeatureField(
        "device_type_icon",
        model_attribute="id",
        # this is a workaround, as django-gisserver check that model attribute is an actual field
        # property is not enough, needs to be checked if this is needed anymore when we update gisserver version.
        xsd_class=IconXsdElement,
        abstract="Device type icon.",
    ),
]
ChunkedQuerySetIterator._restore_caches = replace__restore_caches


class CustomGeoJsonRenderer(GeoJsonRenderer):
    def _format_geojson_value(self, value):
        """Add support for formatting Enums"""
        if isinstance(value, Enum):
            return value.label
        return super()._format_geojson_value(value)

    def render_geometry(self, feature_type, instance: models.Model) -> bytes:
        """Support to convert location to centroid location if supported by the instance"""
        if self._is_centroid_feature_type(feature_type):
            geometry = getattr(instance, "centroid_location", None)
        else:
            geometry = getattr(instance, feature_type.geometry_field.name)
        if geometry is None:
            return b"null"

        self.output_crs.apply_to(geometry)
        return geometry.json.encode()

    @staticmethod
    def _is_centroid_feature_type(feature_type):
        return "centroid" in feature_type.name

    @staticmethod
    def _is_convex_hull_feature_type(instance: models.Model) -> bool:
        """Currently only Plan is represented as convex hull"""
        return hasattr(instance, "convex_hull_location")


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
