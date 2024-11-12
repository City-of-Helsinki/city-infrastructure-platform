from django.conf import settings
from django.contrib.gis import geos
from django.db import models
from gisserver import queries
from gisserver.geometries import BoundingBox
from gisserver.output import GML32Renderer
from gisserver.types import XsdElement

# Non-exhausting list of CRSs with axis order of (latitude longitude)
_YX_CRS = (
    3879,
    4326,
)


def _swap_x_y_bbox(bounding_box: BoundingBox) -> BoundingBox:
    x0, y0 = bounding_box.lower_corner
    x1, y1 = bounding_box.upper_corner
    crs = bounding_box.crs
    return BoundingBox(y0, x0, y1, x1, crs)


def _swap_x_y_coordinates(coordinates):
    return (coordinates[1], coordinates[0], *coordinates[2:])


class SwapBoundingBoxMixin:
    """
    Hack to swap BBOX query parameter to be order of Y/X (latitude/longitude) in such coordinate reference systems.
    """

    def get_query(self, **params) -> queries.QueryExpression:
        if params["STOREDQUERY_ID"]:
            query = params["STOREDQUERY_ID"]
        else:
            if params["bbox"]:
                if params["bbox"].crs:
                    srid = params["bbox"].crs.srid
                else:
                    srid = settings.SRID
                if srid in _YX_CRS:
                    params["bbox"] = _swap_x_y_bbox(params["bbox"])

            query = queries.AdhocQuery.from_kvp_request(**params)

        query.bind(
            all_feature_types=self.all_feature_types_by_name,
            value_reference=params.get("valueReference"),
        )

        return query


class YXGML32Renderer(GML32Renderer):
    """
    Hacky renderer for GML 3.2 that is aware of some coordinate reference systems are
    in order of Y/X (latitude/longitude).
    """

    def _render_gml_type(self, value: geos.GEOSGeometry, base_attrs=""):
        if value.srid not in _YX_CRS:
            return super()._render_gml_type(value, base_attrs)
        else:
            # TODO: Implement other types (currently Cityinfra WFS only serves features with point geometry)
            if isinstance(value, geos.Point):
                return self.render_gml_point(value, base_attrs)

    def render_gml_point(self, value: geos.Point, base_attrs=""):
        coords = " ".join(map(str, _swap_x_y_coordinates(value.coords)))
        dim = 3 if value.hasz else 2
        return f"<gml:Point{base_attrs}>" f'<gml:pos srsDimension="{dim}">{coords}</gml:pos>' f"</gml:Point>"

    def render_bounds(self, feature_type, instance):
        if self.output_crs.srid not in _YX_CRS:
            return super().render_bounds(feature_type, instance)
        else:
            envelope = feature_type.get_envelope(instance, self.output_crs)
            if envelope is not None:
                lower = " ".join(map(str, _swap_x_y_coordinates(envelope.lower_corner)))
                upper = " ".join(map(str, _swap_x_y_coordinates(envelope.upper_corner)))
                return f"""<gml:boundedBy><gml:Envelope srsDimension="2" srsName="{self.xml_srs_name}">
                    <gml:lowerCorner>{lower}</gml:lowerCorner>
                    <gml:upperCorner>{upper}</gml:upperCorner>
                </gml:Envelope></gml:boundedBy>\n"""


class EnumNameXsdElement(XsdElement):
    def get_value(self, instance: models.Model):
        if not (enum_value := getattr(instance, self.name)):
            return None
        return enum_value.name
