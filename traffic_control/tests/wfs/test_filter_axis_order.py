"""Regression tests for the axis ordering of geometries in WFS requests.

django-gisserver 1.5 parsed ``<fes:Filter>`` geometries without axis-order awareness, so their
coordinates were always read as x/y (easting, northing). django-gisserver 2.x reads them
axis-aware, which would flip authority-ordered notations such as ``urn:ogc:def:crs:EPSG::3879``.
``patch_gml_filter_axis_order()`` restores the original behaviour for existing clients.

The ``BBOX`` key-value parameter is a separate code path and has always used the authority
(y/x) ordering for EPSG:3879.
"""

import json
from typing import Optional

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse

from traffic_control.tests.factories import get_api_client, PlanFactory, TrafficSignRealFactory
from traffic_control.tests.utils import MIN_X, MIN_Y
from traffic_control.tests.wfs.wfs_utils import multipoly_inside_bbox, test_bbox_str

# The bounding box that contains `multipoly_inside_bbox`, in x/y (easting, northing) order.
BOX_MIN_X = MIN_X + 2
BOX_MIN_Y = MIN_Y + 10
BOX_MAX_X = MIN_X + 10
BOX_MAX_Y = MIN_Y + 20

BBOX_FILTER = (
    "<Filter><BBOX><PropertyName>location</PropertyName>"
    '<gml:Envelope srsName="{srs}">'
    "<gml:lowerCorner>{lower_x} {lower_y}</gml:lowerCorner>"
    "<gml:upperCorner>{upper_x} {upper_y}</gml:upperCorner>"
    "</gml:Envelope></BBOX></Filter>"
)

INTERSECTS_FILTER = (
    "<Filter><Intersects><PropertyName>location</PropertyName>"
    '<gml:Polygon srsName="{srs}"><gml:exterior><gml:LinearRing><gml:posList>'
    "{lower_x} {lower_y} {lower_x} {upper_y} {upper_x} {upper_y} {upper_x} {lower_y} "
    "{lower_x} {lower_y}"
    "</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></Intersects></Filter>"
)


def _get_number_returned(type_names: str, xml_filter: Optional[str] = None, bbox: Optional[str] = None) -> int:
    """Run a GeoJSON GetFeature request and return the number of returned features.

    Args:
        type_names (str): The WFS feature type to query.
        xml_filter (Optional[str]): An OGC XML ``<Filter>`` document.
        bbox (Optional[str]): A value for the ``BBOX`` key-value parameter.

    Returns:
        int: The ``numberReturned`` value of the response.
    """
    params = {
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "OUTPUTFORMAT": "geojson",
        "TYPENAMES": type_names,
    }
    if xml_filter is not None:
        params["FILTER"] = xml_filter
    if bbox is not None:
        params["BBOX"] = bbox

    response = get_api_client().get(reverse("wfs-city-infrastructure"), params)
    body = b"".join(response.streaming_content).decode()
    assert response.status_code == 200, body[:1500]

    return json.loads(body)["numberReturned"]


@pytest.mark.django_db
@pytest.mark.parametrize("srs", ("urn:ogc:def:crs:EPSG::3879", "EPSG:3879"))
def test__wfs_xml_filter_bbox__uses_xy_order(srs: str):
    """A <gml:Envelope> in a filter is read as x/y, for both the URN and the legacy notation."""
    PlanFactory(location=multipoly_inside_bbox)

    xml_filter = BBOX_FILTER.format(srs=srs, lower_x=BOX_MIN_X, lower_y=BOX_MIN_Y, upper_x=BOX_MAX_X, upper_y=BOX_MAX_Y)

    assert _get_number_returned("plan", xml_filter=xml_filter) == 1


@pytest.mark.django_db
@pytest.mark.parametrize("srs", ("urn:ogc:def:crs:EPSG::3879", "EPSG:3879"))
def test__wfs_xml_filter_bbox__yx_order_does_not_match(srs: str):
    """The same envelope in y/x order falls outside the data, proving the ordering is not swapped."""
    PlanFactory(location=multipoly_inside_bbox)

    xml_filter = BBOX_FILTER.format(
        srs=srs,
        lower_x=BOX_MIN_Y,
        lower_y=BOX_MIN_X,
        upper_x=BOX_MAX_Y,
        upper_y=BOX_MAX_X,
    )

    assert _get_number_returned("plan", xml_filter=xml_filter) == 0


@pytest.mark.django_db
@pytest.mark.parametrize("srs", ("urn:ogc:def:crs:EPSG::3879", "EPSG:3879"))
def test__wfs_xml_filter_intersects__uses_xy_order(srs: str):
    """A <gml:Polygon> in an <Intersects> filter is read as x/y as well."""
    PlanFactory(location=multipoly_inside_bbox)

    xml_filter = INTERSECTS_FILTER.format(
        srs=srs,
        lower_x=BOX_MIN_X,
        lower_y=BOX_MIN_Y,
        upper_x=BOX_MAX_X,
        upper_y=BOX_MAX_Y,
    )

    assert _get_number_returned("plan", xml_filter=xml_filter) == 1


@pytest.mark.django_db
@pytest.mark.parametrize("srs", ("urn:ogc:def:crs:EPSG::4326", "EPSG:4326"))
def test__wfs_xml_filter_bbox__transforms_from_another_crs(srs: str):
    """Filtering with a WGS84 envelope in longitude/latitude order still transforms correctly."""
    location = Point(25496751.5, 6673129.5, 0, srid=3879)
    TrafficSignRealFactory(location=location)
    wgs84_location = location.transform(4326, clone=True)

    xml_filter = BBOX_FILTER.format(
        srs=srs,
        lower_x=wgs84_location.x - 0.01,
        lower_y=wgs84_location.y - 0.01,
        upper_x=wgs84_location.x + 0.01,
        upper_y=wgs84_location.y + 0.01,
    )

    assert _get_number_returned("trafficsignreal", xml_filter=xml_filter) == 1


@pytest.mark.django_db
def test__wfs_kvp_bbox__keeps_yx_order():
    """The BBOX key-value parameter keeps the authority (y/x) ordering of EPSG:3879."""
    PlanFactory(location=multipoly_inside_bbox)

    assert _get_number_returned("plan", bbox=test_bbox_str) == 1
