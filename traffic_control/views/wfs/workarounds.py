"""Backwards compatibility patches for django-gisserver.

These keep the WFS request/response behaviour stable for existing clients across
django-gisserver upgrades. Each patch documents why it exists and when it can be removed.
"""

from django.contrib.gis.gdal import AxisOrder
from gisserver.parsers.gml import GEOSGMLGeometry

_LEGACY_GML_AXIS_ORDER_PATCHED = "_city_infra_legacy_axis_order"


def patch_gml_filter_axis_order() -> None:
    """Read ``<fes:Filter>`` geometries in x/y (easting, northing) order.

    django-gisserver 1.5 parsed filter geometries with ``GEOSGeometry.from_gml()``, which is not
    axis-order aware, so coordinates were always interpreted as x/y regardless of the ``srsName``.
    django-gisserver 2.x parses them axis-aware, which means an authority-ordered notation such as
    ``urn:ogc:def:crs:EPSG::3879`` is read as y/x. Existing clients (including the bundled
    ``map-view`` frontend) send x/y, so without this patch their ``<BBOX>`` and ``<Intersects>``
    filters silently match nothing.

    The patch only affects geometries parsed from XML. The ``BBOX`` key-value parameter is parsed
    by ``GEOSGMLGeometry.from_bbox()`` and keeps its authority (y/x) ordering, which is what this
    service has always used for that parameter.

    Calling this function more than once is a no-op.

    Returns:
        None
    """
    if getattr(GEOSGMLGeometry.from_xml, _LEGACY_GML_AXIS_ORDER_PATCHED, False):
        return

    original_from_xml = GEOSGMLGeometry.from_xml.__func__

    def from_xml(cls, element):
        geometry = original_from_xml(cls, element)
        # Untag the authority axis order so the coordinates are used as-is (x/y).
        geometry.geos_data._axis_order = AxisOrder.TRADITIONAL
        return geometry

    setattr(from_xml, _LEGACY_GML_AXIS_ORDER_PATCHED, True)
    GEOSGMLGeometry.from_xml = classmethod(from_xml)
