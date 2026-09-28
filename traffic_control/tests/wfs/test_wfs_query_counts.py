"""Regression tests ensuring WFS responses do not scale their query count with the feature count."""

from typing import Any, Callable, List, Tuple

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from city_furniture.tests.factories import FurnitureSignpostPlanFactory, FurnitureSignpostRealFactory
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
    geojson_get_features,
    gml_get_features,
    test_point_helsinki,
    wfs_get_features_geojson,
    wfs_get_features_gml,
)

# WFS type name and the factory creating a feature for it
FEATURE_TYPES: List[Tuple[str, Callable]] = [
    ("additionalsignreal", AdditionalSignRealFactory),
    ("additionalsignplan", AdditionalSignPlanFactory),
    ("trafficsignreal", TrafficSignRealFactory),
    ("trafficsignplan", TrafficSignPlanFactory),
    ("signpostreal", SignpostRealFactory),
    ("signpostplan", SignpostPlanFactory),
    ("mountreal", MountRealFactory),
    ("mountrealcentroid", MountRealFactory),
    ("mountplan", MountPlanFactory),
    ("mountplancentroid", MountPlanFactory),
    ("furnituresignpostreal", FurnitureSignpostRealFactory),
    ("furnituresignpostplan", FurnitureSignpostPlanFactory),
]

SMALL_FEATURE_COUNT = 2
LARGE_FEATURE_COUNT = 10


def _create_features(factory: Callable, amount: int) -> None:
    """Create the given amount of features located in Helsinki.

    Args:
        factory (Callable): The factory used to create the features.
        amount (int): How many features to create.
    """
    for _ in range(amount):
        factory(location=test_point_helsinki)


def _count_queries(request_function: Callable, model_name: str) -> Tuple[Any, int]:
    """Perform a WFS GetFeature request and count the database queries it executes.

    Args:
        request_function (Callable): Helper performing the WFS request.
        model_name (str): The WFS type name to request.

    Returns:
        Tuple[Any, int]: The parsed WFS response and the number of executed queries.
    """
    with CaptureQueriesContext(connection) as context:
        response = request_function(model_name)
    return response, len(context.captured_queries)


# Normalize the differing feature extraction signatures to (response, model_name).
REQUEST_FUNCTIONS: List[Tuple[Callable, Callable]] = [
    (wfs_get_features_geojson, lambda response, model_name: geojson_get_features(response)),
    (wfs_get_features_gml, gml_get_features),
]


@pytest.mark.parametrize("model_name, factory", FEATURE_TYPES)
@pytest.mark.parametrize("request_function, get_features", REQUEST_FUNCTIONS)
@pytest.mark.django_db
def test__wfs_query_count_does_not_grow_with_feature_count(
    model_name: str, factory: Callable, request_function: Callable, get_features: Callable
):
    """Rendering more features must not execute more queries.

    A per-feature query (N+1) makes large viewports emit thousands of queries, which is what this
    test guards against.
    """
    _create_features(factory, SMALL_FEATURE_COUNT)

    # Django memoizes the spatial_ref_sys SRID lookup per connection, so the first request in the
    # process executes one extra query. Warm the cache up to keep the measurements comparable.
    request_function(model_name)

    small_response, queries_for_small_response = _count_queries(request_function, model_name)

    _create_features(factory, LARGE_FEATURE_COUNT - SMALL_FEATURE_COUNT)
    large_response, queries_for_large_response = _count_queries(request_function, model_name)

    assert len(get_features(small_response, model_name)) == SMALL_FEATURE_COUNT
    assert len(get_features(large_response, model_name)) == LARGE_FEATURE_COUNT

    assert queries_for_large_response == queries_for_small_response, (
        f"{model_name} executed {queries_for_large_response} queries for {LARGE_FEATURE_COUNT} features "
        f"but {queries_for_small_response} for {SMALL_FEATURE_COUNT}"
    )


@pytest.mark.parametrize("model_name, factory", FEATURE_TYPES)
@pytest.mark.django_db
def test__wfs_response_contains_all_features(model_name: str, factory: Callable):
    """Sanity check that the query count test above actually renders every feature."""
    _create_features(factory, LARGE_FEATURE_COUNT)

    features = geojson_get_features(wfs_get_features_geojson(model_name))

    assert len(features) == LARGE_FEATURE_COUNT
