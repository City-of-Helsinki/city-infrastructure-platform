import pytest
from django.conf import settings
from django.contrib.gis.geos import MultiPolygon, Point, Polygon

from city_furniture.tests.factories import get_furniture_signpost_plan
from traffic_control.tests.factories import (
    get_additional_sign_plan,
    get_barrier_plan,
    get_mount_plan,
    get_plan,
    get_road_marking_plan,
    get_signpost_plan,
    get_traffic_light_plan,
    get_traffic_sign_plan,
)

test_point_outside_area = Point(-20.0, -20.0, 0.0, srid=settings.SRID)
test_multipolygon = MultiPolygon(
    Polygon(
        (
            (20.0, 20.0, 0.0),
            (20.0, 30.0, 0.0),
            (30.0, 30.0, 0.0),
            (30.0, 20.0, 0.0),
            (20.0, 20.0, 0.0),
        ),
        srid=settings.SRID,
    ),
    srid=settings.SRID,
)


@pytest.mark.django_db
def test__plan__get_related_locations():
    plan = get_plan()
    bp_1 = get_barrier_plan(location=Point(10.0, 10.0, 0.0, srid=settings.SRID), plan=plan)
    bp_2 = get_barrier_plan(location=Point(5.0, 5.0, 0.0, srid=settings.SRID), plan=plan)
    mp_1 = get_mount_plan(location=Point(20.0, 5.0, 0.0, srid=settings.SRID), plan=plan)
    mp_2 = get_mount_plan(location=Point(100.0, 10.0, 0.0, srid=settings.SRID), plan=plan)
    rmp_1 = get_road_marking_plan(location=Point(0.0, 50.0, 0.0, srid=settings.SRID), plan=plan)
    rmp_2 = get_road_marking_plan(location=Point(100.0, 100.0, 0.0, srid=settings.SRID), plan=plan)
    sp_1 = get_signpost_plan(location=Point(10.0, 100.0, 0.0, srid=settings.SRID), plan=plan)
    sp_2 = get_signpost_plan(location=Point(35.0, 130.0, 0.0, srid=settings.SRID), plan=plan)
    tlp_1 = get_traffic_light_plan(location=Point(55.0, 120.0, 0.0, srid=settings.SRID), plan=plan)
    tlp_2 = get_traffic_light_plan(location=Point(90.0, 115.0, 0, srid=settings.SRID), plan=plan)
    tsp_1 = get_traffic_sign_plan(location=Point(55.0, 5.0, 0.0, srid=settings.SRID), plan=plan)
    tsp_2 = get_traffic_sign_plan(location=Point(95.0, 110.0, 0.0, srid=settings.SRID), plan=plan)
    asp_1 = get_additional_sign_plan(location=Point(80.0, 120.0, 0.0, srid=settings.SRID), plan=plan)
    asp_2 = get_additional_sign_plan(location=Point(85.0, 125.0, 0.0, srid=settings.SRID), parent=tsp_2, plan=plan)
    fsp_1 = get_furniture_signpost_plan(location=Point(112.0, 112.0, 0.0, srid=settings.SRID), plan=plan)
    fsp_2 = get_furniture_signpost_plan(location=Point(113.0, 113.0, 0.0, srid=settings.SRID), plan=plan)

    locations = plan._get_related_locations()

    assert bp_1.location in locations
    assert bp_2.location in locations
    assert mp_1.location in locations
    assert mp_2.location in locations
    assert rmp_1.location in locations
    assert rmp_2.location in locations
    assert sp_1.location in locations
    assert sp_2.location in locations
    assert tlp_1.location in locations
    assert tlp_2.location in locations
    assert tsp_1.location in locations
    assert tsp_2.location in locations
    assert asp_1.location in locations
    assert asp_2.location in locations
    assert fsp_1.location in locations
    assert fsp_2.location in locations


@pytest.mark.django_db
def test__plan__derive_location_from_related_plans():
    plan = get_plan()
    bp_1 = get_barrier_plan(location=Point(10.0, 10.0, 0.0, srid=settings.SRID), plan=plan)
    bp_2 = get_barrier_plan(location=Point(5.0, 5.0, 0.0, srid=settings.SRID), plan=plan)
    mp_1 = get_mount_plan(location=Point(20.0, 5.0, 0.0, srid=settings.SRID), plan=plan)
    mp_2 = get_mount_plan(location=Point(100.0, 10.0, 0.0, srid=settings.SRID), plan=plan)
    rmp_1 = get_road_marking_plan(location=Point(0.0, 50.0, 0.0, srid=settings.SRID), plan=plan)
    rmp_2 = get_road_marking_plan(location=Point(100.0, 100.0, 0.0, srid=settings.SRID), plan=plan)
    sp_1 = get_signpost_plan(location=Point(10.0, 100.0, 0.0, srid=settings.SRID), plan=plan)
    sp_2 = get_signpost_plan(location=Point(35.0, 130.0, 0.0, srid=settings.SRID), plan=plan)
    tlp_1 = get_traffic_light_plan(location=Point(55.0, 120.0, 0.0, srid=settings.SRID), plan=plan)
    tlp_2 = get_traffic_light_plan(location=Point(90.0, 115.0, 0.0, srid=settings.SRID), plan=plan)
    tsp_1 = get_traffic_sign_plan(location=Point(55.0, 5.0, 0.0, srid=settings.SRID), plan=plan)
    tsp_2 = get_traffic_sign_plan(location=Point(95.0, 110.0, 0.0, srid=settings.SRID), plan=plan)
    asp_1 = get_additional_sign_plan(location=Point(80.0, 120.0, 1.0, srid=settings.SRID), plan=plan)
    asp_2 = get_additional_sign_plan(location=Point(80.0, 120.0, 2.0, srid=settings.SRID), parent=tsp_2, plan=plan)
    fsp_1 = get_furniture_signpost_plan(location=Point(112.0, 112.0, 0.0, srid=settings.SRID), plan=plan)
    fsp_2 = get_furniture_signpost_plan(location=Point(113.0, 113.0, 0.0, srid=settings.SRID), plan=plan)

    noise_bp = get_barrier_plan(location=Point(150.0, 150.0, 0.1, srid=settings.SRID))
    noise_mp = get_mount_plan(location=Point(150.0, 150.0, 0.2, srid=settings.SRID))
    noise_rmp = get_road_marking_plan(location=Point(150.0, 150.0, 0.3, srid=settings.SRID))
    noise_sp = get_signpost_plan(location=Point(150.0, 150.0, 0.4, srid=settings.SRID))
    noise_tlp = get_traffic_light_plan(location=Point(150.0, 150.0, 0.5, srid=settings.SRID))
    noise_tsp = get_traffic_sign_plan(location=Point(150.0, 150.0, 0.6, srid=settings.SRID))
    noise_asp = get_additional_sign_plan(location=Point(150.0, 150.0, 0.7, srid=settings.SRID))
    noise_fsp = get_furniture_signpost_plan(location=Point(150.0, 150.0, 0.8, srid=settings.SRID))

    plan.refresh_from_db()
    plan.derive_location_from_related_plans()

    assert plan.location.contains(bp_1.location)
    assert plan.location.contains(bp_2.location)
    assert plan.location.contains(mp_1.location)
    assert plan.location.contains(mp_2.location)
    assert plan.location.contains(rmp_1.location)
    assert plan.location.contains(rmp_2.location)
    assert plan.location.contains(sp_1.location)
    assert plan.location.contains(sp_2.location)
    assert plan.location.contains(tlp_1.location)
    assert plan.location.contains(tlp_2.location)
    assert plan.location.contains(tsp_1.location)
    assert plan.location.contains(tsp_2.location)
    assert plan.location.contains(asp_1.location)
    assert plan.location.contains(asp_2.location)
    assert plan.location.contains(fsp_1.location)
    assert plan.location.contains(fsp_2.location)
    assert not plan.location.contains(noise_bp.location)
    assert not plan.location.contains(noise_mp.location)
    assert not plan.location.contains(noise_rmp.location)
    assert not plan.location.contains(noise_sp.location)
    assert not plan.location.contains(noise_tlp.location)
    assert not plan.location.contains(noise_tsp.location)
    assert not plan.location.contains(noise_asp.location)
    assert not plan.location.contains(noise_fsp.location)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory",
    (
        get_additional_sign_plan,
        get_barrier_plan,
        get_furniture_signpost_plan,
        get_mount_plan,
        get_road_marking_plan,
        get_signpost_plan,
        get_traffic_light_plan,
        get_traffic_sign_plan,
    ),
)
@pytest.mark.parametrize(
    "derive_location",
    (True, False),
    ids=("derive_location", "no_derive_location"),
)
def test__plan__location_update_on_related_model_save(factory, derive_location: bool):
    plan = get_plan(derive_location=derive_location)
    old_location = plan.location

    related_obj = factory()
    related_obj.plan = plan
    related_obj.save()

    plan.refresh_from_db()
    if derive_location:
        assert plan.location != old_location, "Expected plan location to be updated"
    else:
        assert plan.location == old_location, "Expected plan location to be unchanged"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory",
    (
        get_additional_sign_plan,
        get_barrier_plan,
        get_furniture_signpost_plan,
        get_mount_plan,
        get_road_marking_plan,
        get_signpost_plan,
        get_traffic_light_plan,
        get_traffic_sign_plan,
    ),
)
@pytest.mark.parametrize(
    "derive_location",
    (True, False),
    ids=("derive_location", "no_derive_location"),
)
def test__plan__both_plan_locations_update_when_plan_is_changed(factory, derive_location: bool):
    plan_1 = get_plan(location=test_multipolygon, name="Test plan 1", derive_location=derive_location)
    plan_2 = get_plan(location=test_multipolygon, name="Test plan 2", derive_location=derive_location)
    related_object = factory(location=test_point_outside_area, plan=plan_1)
    plan_1.refresh_from_db()
    if derive_location:
        assert plan_1.location.covers(
            related_object.location
        ), "Expected plan location to cover related object location"
    else:
        assert plan_1.location == test_multipolygon, "Expected plan location to be unchanged"

    related_object.plan = plan_2
    related_object.save()
    plan_1.refresh_from_db()
    plan_2.refresh_from_db()
    if derive_location:
        assert plan_1.location is None, "Expected empty plan_1 location to be None"
    else:
        assert plan_1.location == test_multipolygon, "Expected plan_1 location to be unchanged"
    if derive_location:
        assert plan_2.location.covers(
            related_object.location
        ), "Expected plan_2 location to cover related object location"
    else:
        assert plan_2.location == test_multipolygon, "Expected plan_2 location to be unchanged"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory",
    (
        get_additional_sign_plan,
        get_barrier_plan,
        get_furniture_signpost_plan,
        get_mount_plan,
        get_road_marking_plan,
        get_signpost_plan,
        get_traffic_light_plan,
        get_traffic_sign_plan,
    ),
)
@pytest.mark.parametrize(
    "derive_location",
    (True, False),
    ids=("derive_location", "no_derive_location"),
)
def test__plan__location_update_when_plan_is_removed_from_object(factory, derive_location: bool):
    plan = get_plan(location=test_multipolygon, name="Test plan 1", derive_location=derive_location)
    related_object = factory(plan=plan)
    plan.refresh_from_db()
    if derive_location:
        assert plan.location.covers(related_object.location), "Expected plan location to cover related object location"
    else:
        assert plan.location == test_multipolygon, "Expected plan location to be unchanged"
    related_object.plan = None
    related_object.save()
    plan.refresh_from_db()
    if derive_location:
        assert plan.location is None, "Expected empty plan location to be None"
    else:
        assert plan.location == test_multipolygon, "Expected plan location to be unchanged"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory",
    (
        get_additional_sign_plan,
        get_barrier_plan,
        get_furniture_signpost_plan,
        get_mount_plan,
        get_road_marking_plan,
        get_signpost_plan,
        get_traffic_light_plan,
        get_traffic_sign_plan,
    ),
)
@pytest.mark.parametrize(
    "derive_location",
    (True, False),
    ids=("derive_location", "no_derive_location"),
)
def test__plan__location_update_when_related_object_is_deleted(factory, derive_location: bool):
    plan = get_plan(location=test_multipolygon, name="Test plan", derive_location=derive_location)
    related_object = factory(plan=plan)
    plan.refresh_from_db()
    if derive_location:
        assert plan.location.covers(related_object.location), "Expected plan location to cover related object location"
    else:
        assert plan.location == test_multipolygon, "Expected plan location to be unchanged"

    related_object.delete()
    plan.refresh_from_db()
    if derive_location:
        assert plan.location is None, "Expected empty plan location to be None"
    else:
        assert plan.location == test_multipolygon, "Expected plan location to be unchanged"
