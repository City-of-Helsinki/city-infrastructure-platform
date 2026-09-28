import datetime
from typing import Callable, List, Optional
from xml.etree import ElementTree

import pytest

from city_furniture.tests.factories import FurnitureSignpostPlanFactory, FurnitureSignpostRealFactory
from traffic_control.enums import Lifecycle
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    MountPlanFactory,
    MountRealFactory,
    SignpostPlanFactory,
    SignpostRealFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)
from traffic_control.tests.wfs.wfs_utils import (
    geojson_feature_id,
    geojson_feature_property,
    geojson_get_features,
    gml_feature_id,
    gml_feature_property,
    gml_get_features,
    test_point_helsinki,
    wfs_get_features_geojson,
    wfs_get_features_gml,
)

# WFS type name, plan factory, real factory, name of the plan foreign key on the real model
PLAN_FEATURE_TYPES = [
    ("additionalsignplan", AdditionalSignPlanFactory, AdditionalSignRealFactory, "additional_sign_plan"),
    ("trafficsignplan", TrafficSignPlanFactory, TrafficSignRealFactory, "traffic_sign_plan"),
    ("signpostplan", SignpostPlanFactory, SignpostRealFactory, "signpost_plan"),
    ("mountplan", MountPlanFactory, MountRealFactory, "mount_plan"),
    ("mountplancentroid", MountPlanFactory, MountRealFactory, "mount_plan"),
    ("furnituresignpostplan", FurnitureSignpostPlanFactory, FurnitureSignpostRealFactory, "furniture_signpost_plan"),
]

# Plan models whose real models support validity periods
VALIDITY_PERIOD_FEATURE_TYPES = [params for params in PLAN_FEATURE_TYPES if not params[0].startswith("mountplan")]


def _gml_real_count(model_name: str, plan_id) -> Optional[str]:
    """Read the ``real_count`` property of a single plan feature from the GML response.

    Args:
        model_name (str): The WFS type name, e.g. ``"mountplan"``.
        plan_id: ID of the plan whose feature is looked up.

    Returns:
        Optional[str]: The ``real_count`` property value as text.
    """
    features = gml_get_features(wfs_get_features_gml(model_name), model_name)
    return gml_feature_property(_get_feature(features, model_name, plan_id, gml_feature_id), "real_count")


def _geojson_real_count(model_name: str, plan_id):
    """Read the ``real_count`` property of a single plan feature from the GeoJSON response.

    Args:
        model_name (str): The WFS type name, e.g. ``"mountplan"``.
        plan_id: ID of the plan whose feature is looked up.

    Returns:
        Any: The ``real_count`` property value.
    """
    features = geojson_get_features(wfs_get_features_geojson(model_name))
    return geojson_feature_property(_get_feature(features, model_name, plan_id, geojson_feature_id), "real_count")


def _get_feature(features: List, model_name: str, plan_id, id_getter: Callable):
    """Find the feature matching the given plan ID.

    Args:
        features (List): The features in the WFS response.
        model_name (str): The WFS type name, used to build the expected feature ID.
        plan_id: ID of the plan whose feature is looked up.
        id_getter (Callable): Function returning the feature ID of a single feature.

    Returns:
        The matching feature.

    Raises:
        AssertionError: If no feature matches the given plan ID.
    """
    expected_id = f"{model_name}.{plan_id}"
    matching = [feature for feature in features if id_getter(feature) == expected_id]
    assert len(matching) == 1, f"Expected exactly one feature with id {expected_id}, got {len(matching)}"
    return matching[0]


def _create_plan(plan_factory):
    """Create a device plan located in Helsinki.

    Args:
        plan_factory: The factory used to create the plan.

    Returns:
        The created device plan.
    """
    return plan_factory(location=test_point_helsinki)


@pytest.mark.parametrize("model_name, plan_factory, real_factory, plan_field", PLAN_FEATURE_TYPES)
@pytest.mark.django_db
def test__wfs_plan_real_count__no_reals(model_name: str, plan_factory, real_factory, plan_field: str):
    plan = _create_plan(plan_factory)

    assert _gml_real_count(model_name, plan.id) == "0"
    assert _geojson_real_count(model_name, plan.id) == 0


@pytest.mark.parametrize("model_name, plan_factory, real_factory, plan_field", PLAN_FEATURE_TYPES)
@pytest.mark.django_db
def test__wfs_plan_real_count__counts_related_reals(model_name: str, plan_factory, real_factory, plan_field: str):
    """Each plan only counts the reals referencing it.

    A unique constraint allows at most one active real per plan, so soft deleted reals are used
    here to verify that reals of other plans are not counted either.
    """
    plan = _create_plan(plan_factory)
    other_plan = _create_plan(plan_factory)

    real_factory(location=test_point_helsinki, **{plan_field: plan})
    real_factory(location=test_point_helsinki, is_active=False, **{plan_field: plan})
    real_factory(location=test_point_helsinki, **{plan_field: other_plan})

    assert _gml_real_count(model_name, plan.id) == "1"
    assert _geojson_real_count(model_name, plan.id) == 1
    assert _geojson_real_count(model_name, other_plan.id) == 1


@pytest.mark.parametrize("model_name, plan_factory, real_factory, plan_field", PLAN_FEATURE_TYPES)
@pytest.mark.django_db
def test__wfs_plan_real_count__soft_deleted_real_is_not_counted(
    model_name: str, plan_factory, real_factory, plan_field: str
):
    plan = _create_plan(plan_factory)

    real_factory(location=test_point_helsinki, is_active=False, **{plan_field: plan})

    assert _gml_real_count(model_name, plan.id) == "0"
    assert _geojson_real_count(model_name, plan.id) == 0


@pytest.mark.parametrize("model_name, plan_factory, real_factory, plan_field", PLAN_FEATURE_TYPES)
@pytest.mark.parametrize("lifecycle", (Lifecycle.TEMPORARILY_INACTIVE, Lifecycle.INACTIVE))
@pytest.mark.django_db
def test__wfs_plan_real_count__inactive_lifecycle_real_is_not_counted(
    model_name: str, plan_factory, real_factory, plan_field: str, lifecycle: Lifecycle
):
    plan = _create_plan(plan_factory)

    real_factory(location=test_point_helsinki, lifecycle=lifecycle, **{plan_field: plan})

    assert _gml_real_count(model_name, plan.id) == "0"
    assert _geojson_real_count(model_name, plan.id) == 0


@pytest.mark.parametrize("model_name, plan_factory, real_factory, plan_field", VALIDITY_PERIOD_FEATURE_TYPES)
@pytest.mark.django_db
def test__wfs_plan_real_count__expired_validity_period_real_is_not_counted(
    model_name: str, plan_factory, real_factory, plan_field: str
):
    plan = _create_plan(plan_factory)
    today = datetime.date.today()

    real_factory(
        location=test_point_helsinki,
        validity_period_start=today - datetime.timedelta(days=10),
        validity_period_end=today - datetime.timedelta(days=1),
        **{plan_field: plan},
    )

    assert _gml_real_count(model_name, plan.id) == "0"
    assert _geojson_real_count(model_name, plan.id) == 0


@pytest.mark.parametrize("model_name, plan_factory, real_factory, plan_field", VALIDITY_PERIOD_FEATURE_TYPES)
@pytest.mark.django_db
def test__wfs_plan_real_count__ongoing_validity_period_real_is_counted(
    model_name: str, plan_factory, real_factory, plan_field: str
):
    plan = _create_plan(plan_factory)
    today = datetime.date.today()

    real_factory(
        location=test_point_helsinki,
        validity_period_start=today - datetime.timedelta(days=1),
        validity_period_end=today + datetime.timedelta(days=10),
        **{plan_field: plan},
    )

    assert _gml_real_count(model_name, plan.id) == "1"
    assert _geojson_real_count(model_name, plan.id) == 1


@pytest.mark.parametrize("model_name, plan_factory, real_factory, plan_field", PLAN_FEATURE_TYPES)
@pytest.mark.django_db
def test__wfs_plan_real_count__is_an_integer_element(model_name: str, plan_factory, real_factory, plan_field: str):
    plan = _create_plan(plan_factory)
    real_factory(location=test_point_helsinki, **{plan_field: plan})

    features = gml_get_features(wfs_get_features_gml(model_name), model_name)
    feature: ElementTree.Element = _get_feature(features, model_name, plan.id, gml_feature_id)

    assert int(gml_feature_property(feature, "real_count")) == 1
