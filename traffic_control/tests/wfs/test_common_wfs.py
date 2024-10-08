import pytest
from django.contrib.gis.geos import Point

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.tests.factories import get_furniture_signpost_plan, get_furniture_signpost_real
from traffic_control.models import AdditionalSignPlan, AdditionalSignReal, TrafficSignPlan, TrafficSignReal
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    get_additional_sign_plan,
    get_traffic_sign_plan,
    TrafficSignRealFactory,
)
from traffic_control.tests.wfs.wfs_utils import (
    EPSG_3879_URN,
    geojson_feature_id,
    geojson_get_features,
    gml_feature_id,
    gml_get_features,
    wfs_get_features_geojson,
    wfs_get_features_gml,
)


@pytest.mark.parametrize(
    "model, model_name, factory",
    (
        (TrafficSignPlan, "trafficsignplan", get_traffic_sign_plan),
        (TrafficSignReal, "trafficsignreal", TrafficSignRealFactory),
        (AdditionalSignPlan, "additionalsignplan", get_additional_sign_plan),
        (AdditionalSignReal, "additionalsignreal", AdditionalSignRealFactory),
        (FurnitureSignpostPlan, "furnituresignpostplan", get_furniture_signpost_plan),
        (FurnitureSignpostReal, "furnituresignpostreal", get_furniture_signpost_real),
    ),
)
@pytest.mark.parametrize("bbox_has_crs", (True, False))
@pytest.mark.parametrize("output_format", ("gml", "geojson"))
@pytest.mark.django_db
def test__wfs__get_feature_bounding_box(model, model_name: str, factory, bbox_has_crs, output_format):
    """
    Ensure getting correct set of devices using bounding box filtering
    """

    # BBOX parameter order is (south, west, north, east) in EPSG:3879
    bbox = "10.0,0.0,20.0,10.0"
    if bbox_has_crs:
        bbox += f",{EPSG_3879_URN}"

    # Create two devices, one outside and one inside the bounding box
    factory(location=Point(25, 15, 0, srid=3879))
    device_in = factory(location=Point(5, 15, 0, srid=3879))

    if output_format == "gml":
        response = wfs_get_features_gml(model_name, bbox=bbox)
        features = gml_get_features(response, model_name)
    elif output_format == "geojson":
        response = wfs_get_features_geojson(model_name, bbox=bbox)
        features = geojson_get_features(response)

    assert model.objects.count() == 2
    assert len(features) == 1
    feature = features[0]

    if output_format == "gml":
        feature_id = gml_feature_id(feature)
    elif output_format == "geojson":
        feature_id = geojson_feature_id(feature)

    assert feature_id == f"{model_name}.{device_in.id}"


@pytest.mark.parametrize(
    "model, model_name, factory",
    (
        (TrafficSignPlan, "trafficsignplan", get_traffic_sign_plan),
        (AdditionalSignPlan, "additionalsignplan", get_additional_sign_plan),
    ),
)
@pytest.mark.parametrize("output_format", ("gml", "geojson"))
@pytest.mark.django_db
def test__wfs__replaced_device_plans_are_not_listed(model, model_name: str, factory, output_format):
    """
    Replaced device plans are not listed in WFS response by default
    """

    replaced_device = factory(location=Point(1, 1, 1, srid=3879))
    replacing_device = factory(location=Point(2, 2, 2, srid=3879), replaces=replaced_device)

    if output_format == "gml":
        response = wfs_get_features_gml(model_name)
        features = gml_get_features(response, model_name)
    elif output_format == "geojson":
        response = wfs_get_features_geojson(model_name)
        features = geojson_get_features(response)

    assert model.objects.all().count() == 2
    assert len(features) == 1
    feature = features[0]

    if output_format == "gml":
        feature_id = gml_feature_id(feature)
    elif output_format == "geojson":
        feature_id = geojson_feature_id(feature)

    assert feature_id == f"{model_name}.{replacing_device.id}"
