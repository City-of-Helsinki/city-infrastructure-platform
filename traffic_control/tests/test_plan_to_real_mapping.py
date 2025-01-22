import csv
import os
from tempfile import TemporaryDirectory

import pytest
from django.contrib.gis.geos import Point

from traffic_control.analyze_utils.plan_to_real_mapping import (
    _get_csv_headers,
    _rows_for_results_csv,
    find_and_update_plan_instances_to_reals,
    write_results_to_csv,
)
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    MountPlanFactory,
    MountRealFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)
from traffic_control.tests.test_base_api_3d import test_point_3d

MATCHING_DTYPE_CODE1 = "CODE1"
NOT_MATCHING_DTYPE_CODE = "NOT_MATCHING_CODE"
MATCHING_MOUNT_TYPE_CODE = "MATCHING_MOUNT_CODE"
NOT_MATCHING_MOUNT_TYPE_CODE = "NOT_MATCHING_MOUNT_CODE"
FARAWAY_TEST_POINT = Point(test_point_3d.x + 100, test_point_3d.y + 100, test_point_3d.z, srid=test_point_3d.srid)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("real_factory", "planinstance_factory", "planinstance_field_name", "create_params"),
    (
        (
            TrafficSignRealFactory,
            TrafficSignPlanFactory,
            "traffic_sign_plan",
            {"location": test_point_3d, "device_type__code": MATCHING_DTYPE_CODE1},
        ),
        (
            AdditionalSignRealFactory,
            AdditionalSignPlanFactory,
            "additional_sign_plan",
            {
                "location": test_point_3d,
                "device_type__code": MATCHING_DTYPE_CODE1,
                "parent__device_type__code": MATCHING_DTYPE_CODE1,
            },
        ),
        (
            MountRealFactory,
            MountPlanFactory,
            "mount_plan",
            {"location": test_point_3d, "mount_type__code": MATCHING_MOUNT_TYPE_CODE},
        ),
    ),
)
def test_plan_to_real_mapping__match(real_factory, planinstance_factory, planinstance_field_name, create_params):
    """Test with one real at the same location"""
    real = real_factory(**create_params)
    pi = planinstance_factory(**create_params)
    find_and_update_plan_instances_to_reals(
        real_factory._meta.model, planinstance_factory._meta.model, planinstance_field_name, 0.1, True
    )

    real.refresh_from_db()
    assert getattr(real, planinstance_field_name) == pi


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("real_factory", "planinstance_factory", "planinstance_field_name", "create_params"),
    (
        (
            TrafficSignRealFactory,
            TrafficSignPlanFactory,
            "traffic_sign_plan",
            {"location": test_point_3d, "device_type__code": MATCHING_DTYPE_CODE1},
        ),
        (
            AdditionalSignRealFactory,
            AdditionalSignPlanFactory,
            "additional_sign_plan",
            {
                "location": test_point_3d,
                "device_type__code": MATCHING_DTYPE_CODE1,
                "parent__device_type__code": MATCHING_DTYPE_CODE1,
            },
        ),
        (
            MountRealFactory,
            MountPlanFactory,
            "mount_plan",
            {"location": test_point_3d, "mount_type__code": MATCHING_MOUNT_TYPE_CODE},
        ),
    ),
)
def test_plan_to_real_mapping__three_matches_at_same_location(
    real_factory, planinstance_factory, planinstance_field_name, create_params
):
    """Test 3 plan instance matches with same location, resolution should be done with decision id year and number"""
    real = real_factory(**create_params)
    planinstance_factory(**create_params, plan__decision_id="2023-6")
    planinstance_factory(**create_params, plan__decision_id="2024-2")
    matching_pi = planinstance_factory(**create_params, plan__decision_id="2024-3")
    find_and_update_plan_instances_to_reals(
        real_factory._meta.model, planinstance_factory._meta.model, planinstance_field_name, 0.1, True
    )

    real.refresh_from_db()
    assert getattr(real, planinstance_field_name) == matching_pi


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("real_factory", "planinstance_factory", "planinstance_field_name", "create_params"),
    (
        (
            TrafficSignRealFactory,
            TrafficSignPlanFactory,
            "traffic_sign_plan",
            {"device_type__code": MATCHING_DTYPE_CODE1},
        ),
        (
            AdditionalSignRealFactory,
            AdditionalSignPlanFactory,
            "additional_sign_plan",
            {"device_type__code": MATCHING_DTYPE_CODE1, "parent__device_type__code": MATCHING_DTYPE_CODE1},
        ),
        (
            MountRealFactory,
            MountPlanFactory,
            "mount_plan",
            {"mount_type__code": MATCHING_MOUNT_TYPE_CODE},
        ),
    ),
)
def test_plan_to_real_mapping__location_no_match(
    real_factory, planinstance_factory, planinstance_field_name, create_params
):
    real = real_factory(**create_params, location=FARAWAY_TEST_POINT)
    planinstance_factory(**create_params, location=test_point_3d)
    find_and_update_plan_instances_to_reals(
        real_factory._meta.model, planinstance_factory._meta.model, planinstance_field_name, 0.1, True
    )

    real.refresh_from_db()
    assert getattr(real, planinstance_field_name) is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("real_factory", "planinstance_factory", "planinstance_field_name", "real_create_params", "pi_create_params"),
    (
        (
            TrafficSignRealFactory,
            TrafficSignPlanFactory,
            "traffic_sign_plan",
            {"location": test_point_3d, "device_type__code": NOT_MATCHING_DTYPE_CODE},
            {"location": test_point_3d, "device_type__code": MATCHING_DTYPE_CODE1},
        ),
        (
            AdditionalSignRealFactory,
            AdditionalSignPlanFactory,
            "additional_sign_plan",
            {
                "location": test_point_3d,
                "device_type__code": NOT_MATCHING_DTYPE_CODE,
                "parent__device_type__code": MATCHING_DTYPE_CODE1,
            },
            {
                "location": test_point_3d,
                "device_type__code": MATCHING_DTYPE_CODE1,
                "parent__device_type__code": MATCHING_DTYPE_CODE1,
            },
        ),
        (
            AdditionalSignRealFactory,
            AdditionalSignPlanFactory,
            "additional_sign_plan",
            {
                "location": test_point_3d,
                "device_type__code": MATCHING_DTYPE_CODE1,
                "parent__device_type__code": NOT_MATCHING_DTYPE_CODE,
            },
            {
                "location": test_point_3d,
                "device_type__code": MATCHING_DTYPE_CODE1,
                "parent__device_type__code": MATCHING_DTYPE_CODE1,
            },
        ),
        (
            MountRealFactory,
            MountPlanFactory,
            "mount_plan",
            {"location": test_point_3d, "mount_type__code": NOT_MATCHING_MOUNT_TYPE_CODE},
            {"location": test_point_3d, "mount_type__code": MATCHING_MOUNT_TYPE_CODE},
        ),
    ),
)
def test_plan_to_real_mapping__device_type_no_match(
    real_factory, planinstance_factory, planinstance_field_name, real_create_params, pi_create_params
):
    real = real_factory(**real_create_params)
    planinstance_factory(**pi_create_params)
    find_and_update_plan_instances_to_reals(
        real_factory._meta.model, planinstance_factory._meta.model, planinstance_field_name, 0.1, True
    )

    real.refresh_from_db()
    assert getattr(real, planinstance_field_name) is None


@pytest.mark.django_db
@pytest.mark.parametrize("noise_matches", [False, True])
@pytest.mark.parametrize(
    ("real_factory", "planinstance_factory", "planinstance_field_name", "create_params"),
    (
        (
            TrafficSignRealFactory,
            TrafficSignPlanFactory,
            "traffic_sign_plan",
            {"device_type__code": MATCHING_DTYPE_CODE1},
        ),
        (
            AdditionalSignRealFactory,
            AdditionalSignPlanFactory,
            "additional_sign_plan",
            {"device_type__code": MATCHING_DTYPE_CODE1, "parent__device_type__code": MATCHING_DTYPE_CODE1},
        ),
        (MountRealFactory, MountPlanFactory, "mount_plan", {"mount_type__code": MATCHING_MOUNT_TYPE_CODE}),
    ),
)
def test_plan_to_real_mapping__pi_possbile_in_two_reals(
    real_factory,
    planinstance_factory,
    planinstance_field_name,
    create_params,
    noise_matches,
):
    """Scenario:Real1 has possible match to PlanInstance1, Real2 has possible matches to PlanInstance1 and PlanInstance2
    Expected behavior is that Real2 is mapped with PlanInstance2 and Real1 with PlanInstance1.
    Data setup is like this:
    r1 <-0.5m-> p1 <-0.5m-> r2 <-0.5m-> p2
    so find and update with max_distance 0.6m should find p1 for r1 and p2 for r2
    When there are 2 identical reals, either one of them should be mapped, noise_matches=True parameter is to test this.
    """
    base_pi_location = test_point_3d
    pi_location_1meter_apart = Point(test_point_3d.x + 1, test_point_3d.y, test_point_3d.z, srid=test_point_3d.srid)
    real1_location = Point(test_point_3d.x - 0.5, test_point_3d.y, test_point_3d.z, srid=test_point_3d.srid)
    real2_location = Point(test_point_3d.x + 0.5, test_point_3d.y, test_point_3d.z, srid=test_point_3d.srid)
    real2_noise_location = Point(test_point_3d.x + 2, test_point_3d.y, test_point_3d.z, srid=test_point_3d.srid)

    pi1 = planinstance_factory(location=base_pi_location, **create_params)
    pi2 = planinstance_factory(location=pi_location_1meter_apart, **create_params)

    r1 = real_factory(location=real1_location, **create_params)
    r2 = real_factory(location=real2_location, **create_params)
    real_factory(location=real1_location if noise_matches else real2_noise_location, **create_params)
    find_and_update_plan_instances_to_reals(
        real_factory._meta.model, planinstance_factory._meta.model, planinstance_field_name, 0.6, True
    )

    r1.refresh_from_db()
    r2.refresh_from_db()
    if noise_matches:
        assert getattr(r1, planinstance_field_name) is None
    else:
        assert getattr(r1, planinstance_field_name) == pi1
    assert getattr(r2, planinstance_field_name) == pi2


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("real_factory", "planinstance_factory", "planinstance_field_name", "create_params"),
    (
        (
            TrafficSignRealFactory,
            TrafficSignPlanFactory,
            "traffic_sign_plan",
            {"location": test_point_3d, "device_type__code": MATCHING_DTYPE_CODE1},
        ),
        (
            AdditionalSignRealFactory,
            AdditionalSignPlanFactory,
            "additional_sign_plan",
            {
                "location": test_point_3d,
                "device_type__code": MATCHING_DTYPE_CODE1,
                "parent__device_type__code": MATCHING_DTYPE_CODE1,
            },
        ),
        (
            MountRealFactory,
            MountPlanFactory,
            "mount_plan",
            {"location": test_point_3d, "mount_type__code": MATCHING_MOUNT_TYPE_CODE},
        ),
    ),
)
def test_csv_write(real_factory, planinstance_factory, planinstance_field_name, create_params):
    real_factory(**create_params)
    planinstance_factory(**create_params)
    results, _, _ = find_and_update_plan_instances_to_reals(
        real_factory._meta.model, planinstance_factory._meta.model, planinstance_field_name, 0.1, True
    )
    real_model = real_factory._meta.model
    result_rows = list(_rows_for_results_csv(results, real_model))
    assert len(result_rows) == 1

    with TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, f"{real_model}_results.csv")
        write_results_to_csv(results, real_model, os.path.join(filepath))
        with open(filepath, "r") as f:
            csv_reader = csv.reader(f, delimiter=";")
            for i, row in enumerate(csv_reader):
                if i == 0:
                    # header row
                    assert row == _get_csv_headers(real_model)
                elif i == 1:
                    assert [row] == result_rows
