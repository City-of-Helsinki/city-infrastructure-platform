import pytest

from traffic_control.tests.factories import (
    get_additional_sign_plan,
    get_additional_sign_real,
    get_traffic_sign_plan,
    get_traffic_sign_real,
)


@pytest.mark.parametrize(
    "factory,parent_factory",
    (
        (get_additional_sign_plan, get_traffic_sign_plan),
        (get_additional_sign_real, get_traffic_sign_real),
    ),
)
@pytest.mark.django_db
def test__additional_sign_models__default_to_parent_sign_coordinates(
    factory, parent_factory
):
    parent = parent_factory()
    obj = factory(parent=parent)
    obj.location = None

    obj.save()

    assert obj.location.x == parent.location.x
    assert obj.location.y == parent.location.y
    assert obj.location.srid == parent.location.srid
