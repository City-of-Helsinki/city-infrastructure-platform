from typing import Union

from django.conf import settings
from django.contrib.gis.geos import (
    GeometryCollection,
    GEOSGeometry,
    LinearRing,
    LineString,
    MultiPolygon,
    Point,
    Polygon,
)


def geometry_is_legit(geometry: GEOSGeometry) -> bool:
    return geometry_within_projection_boundary(geometry)


def geometry_within_projection_boundary(geometry: GEOSGeometry) -> bool:
    boundary_polygon = Polygon.from_bbox(settings.SRID_BOUNDARIES.get(settings.SRID))
    return geometry.within(boundary_polygon) if geometry else True


def get_3d_geometry(
    geometry: Union[Point, LinearRing, Polygon, MultiPolygon, LineString], z_coord: float
) -> GEOSGeometry:
    """Get 3d geometry of given geometry with given z-coordinate. Existing z-coord will be overwritten."""
    geom_to_func = {
        Point: get_3d_point,
        LinearRing: get_3d_linearring,
        Polygon: get_3d_polygon,
        MultiPolygon: get_3d_multipolygon,
        LineString: get_3d_linestring,
    }
    if geometry.__class__ not in geom_to_func:
        raise NotImplementedError(f"Could not get 3d geometry from given geometry type: {type(geometry)}")

    return geom_to_func[geometry.__class__](geometry, z_coord)


def get_3d_point(point: Point, z_coord: float) -> Point:
    """Get 3d point of given point with given z-coordinate."""
    return Point(point.x, point.y, z_coord, srid=point.srid)


def get_3d_multipolygon(multipolygon: MultiPolygon, z_coord: float) -> MultiPolygon:
    """Get 3d multipolygon of given point with given z-coordinate."""
    new_polygons = []
    for p in multipolygon:
        new_polygons.append(get_3d_polygon(p, z_coord))
    return MultiPolygon(*new_polygons, srid=multipolygon.srid)


def get_3d_polygon(polygon: Polygon, z_coord: float) -> Polygon:
    """Get 3d polygon of given point with given z-coordinate. Internally polygons are linestrings.
    1st ring is the shell, next ones are holes.
    """
    new_linear_rings = []
    for lr in polygon:
        new_linear_rings.append(get_3d_linearring(lr, z_coord))
    return Polygon(*new_linear_rings, srid=polygon.srid)


def get_3d_linearring(linear_ring: LinearRing, z_coord: float) -> LinearRing:
    """Get 3d linearring of given point with given z-coordinate."""
    new_coords = []
    for coords in linear_ring:
        new_coords.append((coords[0], coords[1], z_coord))
    return LinearRing(new_coords, srid=linear_ring.srid)


def get_3d_linestring(linestring: LineString, z_coord: float) -> LineString:
    """Get 3d point of given point with given z-coordinate."""
    new_coords = []
    for coords in linestring:
        new_coords.append((coords[0], coords[1], z_coord))
    return LineString(new_coords, srid=linestring.srid)


def get_z_for_geometry(geometry):
    """For geometries that have multiple subgeometries z coordinate from the first one is returned."""
    if isinstance(geometry, Point):
        return get_z_for_point(geometry)
    elif isinstance(geometry, LinearRing):
        return get_z_for_linear_ring(geometry)
    elif isinstance(geometry, Polygon):
        return get_z_for_polygon(geometry)
    elif isinstance(geometry, MultiPolygon):
        return get_z_for_multipolygon(geometry)
    elif isinstance(geometry, LineString):
        return get_z_for_linestring(geometry)
    elif isinstance(geometry, GeometryCollection):
        return get_z_for_geometry(geometry[0])
    raise NotImplementedError(f"Could not get z for geometry {type(geometry)}")


def get_z_for_point(point: Point) -> float:
    return point.z


def get_z_for_polygon(polygon: Polygon) -> float:
    """Assumption is that all points have the same z"""
    return get_z_for_linear_ring(polygon[0])


def get_z_for_linear_ring(linear_ring: LinearRing) -> float:
    """Assumption is that all points have the same z"""
    return linear_ring[0][2]


def get_z_for_multipolygon(multipolygon: MultiPolygon) -> float:
    """Assumption is that all points have the same z"""
    return get_z_for_polygon(multipolygon[0])


def get_z_for_linestring(linestring: LineString) -> float:
    """Assumption is that all points have the same z"""
    return linestring[0][2]


def is_simple_geometry(geometry: GEOSGeometry) -> bool:
    return not issubclass(geometry.__class__, GeometryCollection)
