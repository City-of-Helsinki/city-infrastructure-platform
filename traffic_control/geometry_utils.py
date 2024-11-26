from django.conf import settings
from django.contrib.gis.geos import Polygon


def geometry_is_legit(geometry):
    return geometry_within_projection_boundary(geometry)


def geometry_within_projection_boundary(geometry):
    boundary_polygon = Polygon.from_bbox(settings.SRID_BOUNDARIES.get(settings.SRID))
    return geometry.within(boundary_polygon) if geometry else True
