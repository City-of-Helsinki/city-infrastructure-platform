from typing import Optional, Type

from django.conf import settings
from django.contrib.gis.gdal import AxisOrder
from django.db import models
from enumfields import Enum
from gisserver.features import ComplexFeatureField, FeatureField, FeatureType
from gisserver.geometries import CRS
from gisserver.operations.base import OutputFormat
from gisserver.operations.wfs20 import GetFeature
from gisserver.output import GeoJsonRenderer, GML32Renderer
from gisserver.projection import FeatureProjection
from gisserver.types import XsdElement

from traffic_control.views.wfs.utils import (
    AnnotatedIdXsdElement,
    DistanceToPlanXsdElement,
    EnumIntegerNameXsdElement,
    IconXsdElement,
    RealCountXsdElement,
)
from traffic_control.views.wfs.workarounds import patch_gml_filter_axis_order

patch_gml_filter_axis_order()

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
    FeatureField("lifecycle", xsd_class=EnumIntegerNameXsdElement, abstract="Lifecycle of the device."),
]

REPLACEMENT_ANNOTATIONS = {
    "wfs_replaced_by": models.F("replacement_to_new__new"),
    "wfs_replaces": models.F("replacement_to_old__old"),
}

REPLACEABLE_MODEL_FIELDS = [
    FeatureField(
        "replaced_by",
        model_attribute="id",
        # Bound to a local field on purpose; the value comes from the `wfs_replaced_by` annotation.
        # Binding it to the `replacement_to_new.new` relation makes django-gisserver prefetch the
        # replacement table with one ID per rendered feature, which produces huge statements.
        xsd_class=AnnotatedIdXsdElement,
        abstract="ID of the device plan which replaces this device plan",
    ),
    FeatureField(
        "replaces",
        model_attribute="id",
        # Value comes from the `wfs_replaces` annotation, see the note above.
        xsd_class=AnnotatedIdXsdElement,
        abstract="ID of the device plan which this device plan replaces",
    ),
]

REAL_COUNT_FIELDS = [
    FeatureField(
        "real_count",
        model_attribute="id",
        # This is a workaround, as django-gisserver checks that the model attribute is an actual
        # model field; the value itself comes from the queryset's `real_count` annotation.
        xsd_class=RealCountXsdElement,
        abstract="Number of reals that realize this device plan.",
    ),
]

DISTANCE_TO_PLAN_FIELDS = [
    FeatureField(
        "distance_to_plan",
        model_attribute="id",
        # This is a workaround, as django-gisserver checks that the model attribute is an actual
        # model field; the value itself comes from the queryset's `distance_to_plan` annotation.
        xsd_class=DistanceToPlanXsdElement,
        abstract="Distance in meters between this device and the device plan it realizes.",
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
        model_attribute="device_type.icon_file",
        # Bound to the icon relation so django-gisserver includes it in the projection and resolves
        # it with the main query. IconXsdElement renders the icon's file name from it.
        xsd_class=IconXsdElement,
        abstract="Device type icon.",
    ),
]


class CustomGeoJsonRenderer(GeoJsonRenderer):
    def _format_geojson_value(self, value):
        """Add support for formatting Enums"""
        if isinstance(value, Enum):
            return value.label
        return super()._format_geojson_value(value)

    def render_geometry(self, projection: FeatureProjection, instance: models.Model) -> bytes:
        """Render the main geometry, honouring custom ``XsdElement.get_value()`` implementations.

        The default implementation reads the geometry through the ORM path of the element, which
        bypasses elements such as ``CentroidLocationXsdElement`` that expose a model property
        instead of a database field.

        Args:
            projection: The feature projection that is being rendered.
            instance: The Django model instance to render the geometry for.

        Returns:
            bytes: The GeoJSON encoded geometry, or ``b"null"`` when there is no geometry.
        """
        geometry = self._get_geometry(projection, instance)
        if geometry is None:
            return b"null"

        # GeoJSON always uses x/y (longitude/latitude) ordering.
        projection.output_crs.apply_to(geometry, axis_order=AxisOrder.TRADITIONAL)
        return geometry.json.encode()

    @staticmethod
    def _get_geometry(projection: FeatureProjection, instance: models.Model):
        """Resolve the geometry value that should be rendered for an instance.

        Args:
            projection: The feature projection that is being rendered.
            instance: The Django model instance to read the geometry from.

        Returns:
            GEOSGeometry | None: The geometry to render, or ``None`` when there is none.
        """
        geo_element = projection.main_geometry_element
        if geo_element is None:
            return None
        return geo_element.get_value(instance)


class CustomGetFeature(GetFeature):
    def get_output_formats(self) -> list[OutputFormat]:
        """List the supported output formats for ``GetFeature``.

        Database-side rendering is intentionally not used, because the custom geometry elements
        (e.g. centroid) resolve their value in Python through ``get_value()``.

        Returns:
            list[OutputFormat]: The output formats offered by this operation.
        """
        return [
            OutputFormat("application/gml+xml", version="3.2", renderer_class=GML32Renderer, title="GML"),
            OutputFormat("text/xml", subtype="gml/3.2.1", renderer_class=GML32Renderer, title="GML 3.2.1"),
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
        parent: Optional[ComplexFeatureField] = None,
        feature_type: Optional[FeatureType] = None,
        abstract=None,
        xsd_class: Optional[Type[XsdElement]] = None,
        description: str = "",
    ):
        self.description = description
        super().__init__(
            name,
            model_attribute=model_attribute,
            model=model,
            parent=parent,
            feature_type=feature_type,
            abstract=abstract,
            xsd_class=xsd_class,
        )
