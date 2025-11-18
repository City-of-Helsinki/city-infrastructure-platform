import pytest
from django.contrib.gis.geos import Point
from django.utils import timezone

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.tests.factories import get_furniture_signpost_plan, get_furniture_signpost_real
from traffic_control.models import AdditionalSignPlan, AdditionalSignReal, Plan, TrafficSignPlan, TrafficSignReal
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    get_additional_sign_plan_and_replace,
    get_traffic_sign_plan,
    PlanFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)
from traffic_control.tests.utils import MIN_X, MIN_Y
from traffic_control.tests.wfs.wfs_utils import (
    EPSG_3879_URN,
    geojson_feature_id,
    geojson_get_features,
    gml_feature_id,
    gml_get_features,
    multipoly_inside_bbox,
    multipoly_outside_bbox,
    point_inside_bbox,
    point_outside_bbox,
    test_bbox_str,
    wfs_get_features_geojson,
    wfs_get_features_gml,
)


@pytest.mark.parametrize(
    "model, model_name, factory, geom_outsidebbox, geom_insidebbox",
    (
        (TrafficSignPlan, "trafficsignplan", get_traffic_sign_plan, point_outside_bbox, point_inside_bbox),
        (TrafficSignReal, "trafficsignreal", TrafficSignRealFactory, point_outside_bbox, point_inside_bbox),
        (
            AdditionalSignPlan,
            "additionalsignplan",
            get_additional_sign_plan_and_replace,
            point_outside_bbox,
            point_inside_bbox,
        ),
        (AdditionalSignReal, "additionalsignreal", AdditionalSignRealFactory, point_outside_bbox, point_inside_bbox),
        (
            FurnitureSignpostPlan,
            "furnituresignpostplan",
            get_furniture_signpost_plan,
            point_outside_bbox,
            point_inside_bbox,
        ),
        (
            FurnitureSignpostReal,
            "furnituresignpostreal",
            get_furniture_signpost_real,
            point_outside_bbox,
            point_inside_bbox,
        ),
        (Plan, "plan", PlanFactory, multipoly_outside_bbox, multipoly_inside_bbox),
    ),
)
@pytest.mark.parametrize("bbox_has_crs", (True, False))
@pytest.mark.parametrize("output_format", ("gml", "geojson"))
@pytest.mark.django_db
def test__wfs__get_feature_bounding_box(
    model, model_name: str, factory, bbox_has_crs, output_format, geom_outsidebbox, geom_insidebbox
):
    """
    Ensure getting correct set of devices using bounding box filtering
    """

    # BBOX parameter order is (south, west, north, east) in EPSG:3879
    bbox = test_bbox_str
    if bbox_has_crs:
        bbox += f",{EPSG_3879_URN}"

    # Create two devices, one outside and one inside the bounding box
    factory(location=geom_outsidebbox)
    device_in = factory(location=geom_insidebbox)

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
        (AdditionalSignPlan, "additionalsignplan", get_additional_sign_plan_and_replace),
    ),
)
@pytest.mark.parametrize("output_format", ("gml", "geojson"))
@pytest.mark.django_db
def test__wfs__replaced_device_plans_are_not_listed(model, model_name: str, factory, output_format):
    """
    Replaced device plans are not listed in WFS response by default
    """

    replaced_device = factory(location=Point(MIN_X + 1, MIN_Y + 1, 1, srid=3879))
    replacing_device = factory(location=Point(MIN_X + 2, MIN_Y + 2, 2, srid=3879), replaces=replaced_device)

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


@pytest.mark.parametrize(
    "model, model_name, factory",
    (
        (AdditionalSignPlan, "additionalsignplan", get_additional_sign_plan_and_replace),
        (AdditionalSignReal, "additionalsignreal", AdditionalSignRealFactory),
        (TrafficSignPlan, "trafficsignplan", TrafficSignPlanFactory),
        (TrafficSignReal, "trafficsignreal", TrafficSignRealFactory),
        # Add other models here if they use the same validity period queryset logic
    ),
)
@pytest.mark.parametrize(
    "start_delta, end_delta, expect_included",
    [
        (None, None, True),  # start=None, end=None
        (-1, None, True),  # start in past, end=None
        (1, None, False),  # start in future, end=None
        (None, -1, False),  # start=None, end in past
        (None, 1, True),  # start=None, end in future
        (-1, -1, False),  # start in past, end in past
        (-1, 1, True),  # start in past, end in future
        (1, -1, False),  # start in future, end in past
        (1, 1, False),  # start in future, end in future
    ],
)
@pytest.mark.django_db
def test__wfs__validity_period_combinations(model, model_name, factory, start_delta, end_delta, expect_included):
    """
    WFS API should include/exclude objects based on all combinations of validity_period_start and validity_period_end.
    """
    now = timezone.now()
    validity_period_start = now + timezone.timedelta(days=start_delta) if start_delta is not None else None
    validity_period_end = now + timezone.timedelta(days=end_delta) if end_delta is not None else None
    obj = factory(validity_period_start=validity_period_start, validity_period_end=validity_period_end)
    response = wfs_get_features_geojson(model_name)
    features = geojson_get_features(response)
    included = any(f["id"] == f"{model_name}.{obj.id}" for f in features)
    assert included == expect_included
