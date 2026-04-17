import pytest

from city_furniture.tests.factories import (
    CityFurnitureDeviceTypeFactory,
    FurnitureSignpostPlanFactory,
    FurnitureSignpostRealFactory,
)
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    BarrierPlanFactory,
    BarrierRealFactory,
    get_api_client,
    get_user,
    MountPlanFactory,
    MountRealFactory,
    MountTypeFactory,
    OwnerFactory,
    PlanFactory,
    ResponsibleEntityFactory,
    RoadMarkingPlanFactory,
    RoadMarkingRealFactory,
    SignpostPlanFactory,
    SignpostRealFactory,
    TrafficLightPlanFactory,
    TrafficLightRealFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)

ITEM_COUNT = 50
MAX_ALLOWED_QUERIES = 20

ENDPOINT_MAPPINGS = [
    ("/v1/additional-sign-plans/", AdditionalSignPlanFactory),
    ("/v1/additional-sign-reals/", AdditionalSignRealFactory),
    ("/v1/barrier-plans/", BarrierPlanFactory),
    ("/v1/barrier-reals/", BarrierRealFactory),
    ("/v1/city-furniture-device-types/", CityFurnitureDeviceTypeFactory),
    ("/v1/furniture-signpost-plans/", FurnitureSignpostPlanFactory),
    ("/v1/furniture-signpost-reals/", FurnitureSignpostRealFactory),
    ("/v1/mount-plans/", MountPlanFactory),
    ("/v1/mount-reals/", MountRealFactory),
    ("/v1/mount-types/", MountTypeFactory),
    ("/v1/owners/", OwnerFactory),
    ("/v1/plans/", PlanFactory),
    ("/v1/responsible-entity/", ResponsibleEntityFactory),
    ("/v1/road-marking-plans/", RoadMarkingPlanFactory),
    ("/v1/road-marking-reals/", RoadMarkingRealFactory),
    ("/v1/signpost-plans/", SignpostPlanFactory),
    ("/v1/signpost-reals/", SignpostRealFactory),
    ("/v1/traffic-light-plans/", TrafficLightPlanFactory),
    ("/v1/traffic-light-reals/", TrafficLightRealFactory),
    ("/v1/traffic-sign-plans/", TrafficSignPlanFactory),
    ("/v1/traffic-sign-reals/", TrafficSignRealFactory),
]


@pytest.mark.django_db
@pytest.mark.parametrize("endpoint, factory_class", ENDPOINT_MAPPINGS)
def test_endpoint_query_counts(django_assert_max_num_queries, endpoint, factory_class):
    """
    Ensures that fetching 50 items does not trigger N+1 queries.
    An optimized endpoint with select_related/prefetch_related should typically take less than 10-15 queries.
    """
    factory_class.create_batch(ITEM_COUNT)
    user = get_user("test_user_admin", admin=True)
    client = get_api_client(user=user)
    url = f"{endpoint}?limit={ITEM_COUNT}"

    with django_assert_max_num_queries(MAX_ALLOWED_QUERIES):
        response = client.get(url)

    assert response.status_code == 200
    response_data = response.json()

    # Loose fit because some models seem to have pre-created objects, and this test is about number of queries. There
    # are better tests for testing API correctness
    assert len(response_data.get("results", [])) >= ITEM_COUNT
