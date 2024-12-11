import json
from typing import List, Optional, Union
from urllib.parse import urlencode
from xml.etree import ElementTree

from django.conf import settings
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status

from traffic_control.tests.factories import get_api_client

test_point_helsinki = Point(25496751.5, 6673129.5, 1.5, srid=3879)


EPSG_3879_URN = "urn:ogc:def:crs:EPSG::3879"

namespaces = {
    "app": f"http://{settings.HOSTNAME}/wfs",
    "wfs": "http://www.opengis.net/wfs/2.0",
    "gml": "http://www.opengis.net/gml/3.2",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

MULTI_GEOMETRIES = ["MultiPolygon", "MultiPoint", "MultiLineString", "GeometryCollection"]


def wfs_url_get_features(
    type_names: Union[str, List[str]],
    srs_name: Optional[str] = None,
    output_format: Optional[str] = None,
    bbox: Optional[str] = None,
) -> str:
    base_url = f"{reverse('wfs-city-infrastructure')}?"

    if isinstance(type_names, list):
        type_names = ",".join(type_names)

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": type_names,
        "outputFormat": output_format,
        "srsName": srs_name,
        "bbox": bbox,
    }

    non_none_params = {k: v for k, v in params.items() if v is not None}

    return base_url + urlencode(non_none_params)


def wfs_get_features_gml(
    model_name,
    bbox: Optional[str] = None,
) -> ElementTree.Element:
    client = get_api_client()

    response = client.get(wfs_url_get_features(model_name, bbox=bbox))
    assert response.status_code == status.HTTP_200_OK

    xml = get_response_content(response)

    return ElementTree.fromstring(xml)


def wfs_get_features_geojson(
    model_name,
    bbox: Optional[str] = None,
) -> dict:
    client = get_api_client()

    response = client.get(wfs_url_get_features(model_name, output_format="geojson", bbox=bbox))
    assert response.status_code == status.HTTP_200_OK

    geojson = get_response_content(response)
    return json.loads(geojson)


def get_response_content(response) -> str:
    streaming_content = list(response.streaming_content)
    assert len(streaming_content) == 1

    content = streaming_content[0]
    return content.decode("utf8")


# --- GML ---#


def gml_get_features(element: ElementTree.Element, model_name: str) -> List[ElementTree.Element]:
    return element.findall(f"./wfs:member/app:{model_name}", namespaces)


def gml_feature_id(feature_element: ElementTree.Element):
    return feature_element.get(f"{{{namespaces['gml']}}}id")


def gml_feature_geometry(feature_element: ElementTree.Element, geometry_type="Point"):
    geom_element = feature_element.find(_get_xpath_for_geometry_position(geometry_type), namespaces)
    text = geom_element.text
    return text if text else ElementTree.tostring(geom_element, encoding="unicode")


def gml_feature_crs(feature_element: ElementTree.Element, geometry_type="Point"):
    return feature_element.find(
        f"./app:location/gml:{'MultiGeometry' if geometry_type in MULTI_GEOMETRIES else geometry_type}", namespaces
    ).get("srsName")


def gml_envelope(feature_element: ElementTree.Element):
    lower_corner = feature_element.find("./gml:boundedBy/gml:Envelope/gml:lowerCorner", namespaces).text
    upper_corner = feature_element.find("./gml:boundedBy/gml:Envelope/gml:upperCorner", namespaces).text
    return lower_corner, upper_corner


def _get_xpath_for_geometry_position(geometry_type: str):
    if geometry_type == "Point":
        return "./app:location/gml:Point/gml:pos"
    elif geometry_type == "Polygon":
        return "./app:location/gml:Polygon/gml:exterior/gml:LinearRing/gml:posList"
    elif geometry_type in MULTI_GEOMETRIES:
        return "./app:location/gml:MultiGeometry"
    elif geometry_type == "LineString":
        return "./app:location/gml:LineString/gml:posList"

    raise NotImplementedError(f"Getting gml position for {geometry_type} not implemented")


# --- GeoJSON --- #


def geojson_get_features(geojson: dict) -> List[dict]:
    return geojson["features"]


def geojson_crs(geojson) -> str:
    return geojson["crs"]["properties"]["name"]


def geojson_feature_id(feature: dict) -> str:
    return feature["id"]


def geojson_feature_point_coordinates(feature: dict) -> List[float]:
    assert feature["geometry"]["type"] == "Point"
    return feature["geometry"]["coordinates"]
