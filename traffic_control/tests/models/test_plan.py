import pytest
from django.conf import settings
from django.contrib.gis.geos import Point

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


@pytest.mark.django_db
def test_plan_get_related_locations():
    plan = get_plan()
    bp_1 = get_barrier_plan(location=Point(10.0, 10.0, srid=settings.SRID), plan=plan)
    bp_2 = get_barrier_plan(location=Point(5.0, 5.0, srid=settings.SRID), plan=plan)
    mp_1 = get_mount_plan(location=Point(20.0, 5.0, srid=settings.SRID), plan=plan)
    mp_2 = get_mount_plan(location=Point(100.0, 10.0, srid=settings.SRID), plan=plan)
    rmp_1 = get_road_marking_plan(
        location=Point(0.0, 50.0, srid=settings.SRID), plan=plan
    )
    rmp_2 = get_road_marking_plan(
        location=Point(100.0, 100.0, srid=settings.SRID), plan=plan
    )
    sp_1 = get_signpost_plan(location=Point(10.0, 100.0, srid=settings.SRID), plan=plan)
    sp_2 = get_signpost_plan(location=Point(35.0, 130.0, srid=settings.SRID), plan=plan)
    tlp_1 = get_traffic_light_plan(
        location=Point(55.0, 120.0, srid=settings.SRID), plan=plan
    )
    tlp_2 = get_traffic_light_plan(
        location=Point(90.0, 115.0, srid=settings.SRID), plan=plan
    )
    tsp_1 = get_traffic_sign_plan(
        location=Point(55.0, 5.0, 0.0, srid=settings.SRID), plan=plan
    )
    tsp_2 = get_traffic_sign_plan(
        location=Point(95.0, 110.0, 0.0, srid=settings.SRID), plan=plan
    )
    asp_1 = get_additional_sign_plan(
        location=Point(80.0, 120.0, 0.0, srid=settings.SRID), plan=plan
    )
    asp_2 = get_additional_sign_plan(
        location=Point(80.0, 120.0, 0.0, srid=settings.SRID), parent=tsp_2, plan=plan
    )

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


@pytest.mark.django_db
def test_plan_derive_location_from_related_plans():
    plan = get_plan()
    bp_1 = get_barrier_plan(location=Point(10.0, 10.0, srid=settings.SRID), plan=plan)
    bp_2 = get_barrier_plan(location=Point(5.0, 5.0, srid=settings.SRID), plan=plan)
    mp_1 = get_mount_plan(location=Point(20.0, 5.0, srid=settings.SRID), plan=plan)
    mp_2 = get_mount_plan(location=Point(100.0, 10.0, srid=settings.SRID), plan=plan)
    rmp_1 = get_road_marking_plan(
        location=Point(0.0, 50.0, srid=settings.SRID), plan=plan
    )
    rmp_2 = get_road_marking_plan(
        location=Point(100.0, 100.0, srid=settings.SRID), plan=plan
    )
    sp_1 = get_signpost_plan(location=Point(10.0, 100.0, srid=settings.SRID), plan=plan)
    sp_2 = get_signpost_plan(location=Point(35.0, 130.0, srid=settings.SRID), plan=plan)
    tlp_1 = get_traffic_light_plan(
        location=Point(55.0, 120.0, srid=settings.SRID), plan=plan
    )
    tlp_2 = get_traffic_light_plan(
        location=Point(90.0, 115.0, srid=settings.SRID), plan=plan
    )
    tsp_1 = get_traffic_sign_plan(
        location=Point(55.0, 5.0, 0.0, srid=settings.SRID), plan=plan
    )
    tsp_2 = get_traffic_sign_plan(
        location=Point(95.0, 110.0, 0.0, srid=settings.SRID), plan=plan
    )
    asp_1 = get_additional_sign_plan(
        location=Point(80.0, 120.0, 0.0, srid=settings.SRID)
    )
    asp_2 = get_additional_sign_plan(
        location=Point(80.0, 120.0, 0.0, srid=settings.SRID), parent=tsp_2
    )

    noise_bp = get_barrier_plan(location=Point(150.0, 150.0, srid=settings.SRID))
    noise_mp = get_mount_plan(location=Point(150.0, 150.0, srid=settings.SRID))
    noise_rmp = get_road_marking_plan(location=Point(150.0, 150.0, srid=settings.SRID))
    noise_sp = get_signpost_plan(location=Point(150.0, 150.0, srid=settings.SRID))
    noise_tlp = get_traffic_light_plan(location=Point(150.0, 150.0, srid=settings.SRID))
    noise_tsp = get_traffic_sign_plan(
        location=Point(150.0, 150.0, 0.0, srid=settings.SRID)
    )
    noise_asp = get_additional_sign_plan(
        location=Point(150.0, 150.0, 0.0, srid=settings.SRID)
    )

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
    assert not plan.location.contains(noise_bp.location)
    assert not plan.location.contains(noise_mp.location)
    assert not plan.location.contains(noise_rmp.location)
    assert not plan.location.contains(noise_sp.location)
    assert not plan.location.contains(noise_tlp.location)
    assert not plan.location.contains(noise_tsp.location)
    assert not plan.location.contains(noise_asp.location)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory",
    (
        get_barrier_plan,
        get_mount_plan,
        get_road_marking_plan,
        get_signpost_plan,
        get_traffic_light_plan,
        get_traffic_sign_plan,
    ),
)
def test_plan_location_is_updated_on_related_model_save(factory):
    plan = get_plan()
    old_location = plan.location

    related_obj = factory()
    related_obj.plan = plan
    related_obj.save()

    plan.refresh_from_db()
    assert plan.location != old_location
