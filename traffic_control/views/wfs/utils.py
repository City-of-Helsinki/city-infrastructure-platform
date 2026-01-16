import itertools

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
            if isinstance(value, geos.Point):
                return self.render_gml_point(value, base_attrs)
            elif isinstance(value, geos.LinearRing):
                return self.render_gml_linear_ring(value, base_attrs)
            elif isinstance(value, geos.LineString):
                return self.render_gml_line_string(value, base_attrs)
            elif isinstance(value, geos.GeometryCollection):
                return self.render_gml_multi_geometry(value, base_attrs)
            else:
                return super()._render_gml_type(value, base_attrs)

    def render_gml_point(self, value: geos.Point, base_attrs=""):
        coords = " ".join(map(str, _swap_x_y_coordinates(value.coords)))
        dim = 3 if value.hasz else 2
        return f"<gml:Point{base_attrs}>" f'<gml:pos srsDimension="{dim}">{coords}</gml:pos>' f"</gml:Point>"

    @staticmethod
    def get_swapped_coordinates(value):
        coords = list(map(str, itertools.chain.from_iterable(value.tuple)))
        new_coords = []
        dim = "3" if value.hasz else "2"

        start_index = 0
        step = int(dim)
        end_index = start_index + step
        while end_index <= len(coords):
            new_coords.extend(_swap_x_y_coordinates(coords[start_index:end_index]))
            start_index += step
            end_index += step

        return new_coords, dim

    def render_gml_linear_ring(self, value: geos.LinearRing, base_attrs=""):
        # NOTE: this is super slow. value.tuple performs a C-API call for every point!
        coords, dim = self.get_swapped_coordinates(value)
        # <gml:coordinates> is still valid in GML3, but deprecated (part of GML2).
        return (
            f"<gml:LinearRing{base_attrs}>"
            f'<gml:posList srsDimension="{dim}">{" ".join(coords)}</gml:posList>'
            "</gml:LinearRing>"
        )

    def render_gml_line_string(self, value: geos.LineString, base_attrs=""):
        # NOTE: this is super slow. value.tuple performs a C-API call for every point!
        coords, dim = self.get_swapped_coordinates(value)
        return (
            f"<gml:LineString{base_attrs}>"
            f'<gml:posList srsDimension="{dim}">{" ".join(coords)}</gml:posList>'
            "</gml:LineString>"
        )

    def write_bounds(self, projection, instance):
        if self.output_crs.srid not in _YX_CRS:
            return super().write_bounds(projection, instance)
        else:
            envelope = projection.feature_type.get_envelope(instance, self.output_crs)
            if envelope is not None:
                lower = " ".join(map(str, _swap_x_y_coordinates(envelope.lower_corner)))
                upper = " ".join(map(str, _swap_x_y_coordinates(envelope.upper_corner)))
                self._write(
                    f"""<gml:boundedBy><gml:Envelope srsDimension="2" srsName="{self.xml_srs_name}">
                    <gml:lowerCorner>{lower}</gml:lowerCorner>
                    <gml:upperCorner>{upper}</gml:upperCorner>
                </gml:Envelope></gml:boundedBy>\n"""
                )


class EnumNameXsdElement(XsdElement):
    def get_value(self, instance: models.Model):
        if not (enum_value := getattr(instance, self.name)):
            return None
        return enum_value.name


class CentroidLocationXsdElement(XsdElement):
    def get_value(self, instance: models.Model):
        return getattr(instance, "centroid_location", None)


class ConvexHullLocationXsdElement(XsdElement):
    def get_value(self, instance: models.Model):
        return getattr(instance, "convex_hull_location", None)


class IconXsdElement(XsdElement):
    def get_value(self, instance: models.Model):
        # instance needs to have device_type field
        if instance.device_type and instance.device_type.icon_file:
            return instance.device_type.icon_name
        return None


class ContentSRowSElement(XsdElement):
    def get_value(self, instance: models.Model):
        # instance needs to have content_s_rows attribute
        if hasattr(instance, "content_s"):
            return instance.get_content_s_rows()
        return None
