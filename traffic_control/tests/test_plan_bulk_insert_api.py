import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.settings import api_settings

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import (
    AdditionalSignPlan,
    MountPlan,
    Plan,
    SignpostPlan,
    TrafficControlDeviceType,
    TrafficSignPlan,
)
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    MountPlanFactory,
    OwnerFactory,
    PlanFactory,
    SignpostPlanFactory,
    TrafficSignPlanFactory,
)

DEFAULT_PLAN_ID = "00000000-0000-4000-0000-000000000000"
DEFAULT_MOUNT_PLAN_ID = "11111111-1111-4111-1111-111111111111"
DEFAULT_SIGNPOST_PLAN_ID = "22222222-2222-4222-2222-222222222222"
DEFAULT_TRAFFIC_SIGN_PLAN_ID = "33333333-3333-4333-3333-333333333333"
DEFAULT_ADDITIONAL_SIGN_PLAN_ID = "44444444-4444-4444-4444-444444444444"
ALT_MOUNT_PLAN_ID = "11111111-1111-4111-1111-ffffffffffff"
ALT_SIGNPOST_PLAN_ID = "22222222-2222-4222-2222-ffffffffffff"
NON_EXISTENT_ID = "ffffffff-ffff-4fff-ffff-ffffffffffff"

MULTIPOLYGON = (
    "SRID=3879;MULTIPOLYGON Z (((25497733.5 6672927.5 0, 25497946.5 6673032.5 0, 25498653.5 6673034.5 0, 25498987.5 "
    "6672708.5 0, 25498314.5 6672170.5 0, 25497651.5 6672629.5 0, 25497646.5 6672775.5 0, 25497733.5 6672927.5 0)))"
)
POINT = "SRID=3879;POINT Z (25496751.5 6673129.5 1.5)"

NON_FIELD_ERRORS = api_settings.NON_FIELD_ERRORS_KEY


def additional_sign_plan_payload(
    *,
    device_type,
    owner,
    location=POINT,
    mount_plan=DEFAULT_MOUNT_PLAN_ID,
    request_object_id=DEFAULT_ADDITIONAL_SIGN_PLAN_ID,
    parent=DEFAULT_TRAFFIC_SIGN_PLAN_ID,
    plan=DEFAULT_PLAN_ID,
    **kwargs,
) -> dict:
    result = {
        "id": request_object_id,
        "device_type": device_type,
        "location": location,
        "mount_plan": mount_plan,
        "owner": owner,
        "parent": parent,
        "plan": plan,
        "additional_information": "Example additional sign for v1/plans/bulk-insert operation",
        "missing_content": False,
        "seasonal_validity_period_information": "",
    }
    result.update(kwargs)
    return result


def mount_plan_payload(
    *,
    location=MULTIPOLYGON,
    request_object_id=DEFAULT_MOUNT_PLAN_ID,
    owner,
    plan=DEFAULT_PLAN_ID,
    **kwargs,
) -> dict:
    result = {
        "id": request_object_id,
        "owner": owner,
        "plan": plan,
        "base": "Concrete",
        "lifecycle": 3,
        "location": location,
        "txt": "Example mount plan for v1/plans/bulk-insert operation",
    }
    result.update(kwargs)
    return result


def plan_payload(*, request_object_id=DEFAULT_PLAN_ID, **kwargs) -> dict:
    result = {
        "id": request_object_id,
        "name": "Example plan for v1/plans/bulk-insert operation",
        "decision_id": "DEC-2026",
        "drawing_numbers": [],
        "derive_location": True,
    }
    result.update(kwargs)
    return result


def signpost_plan_payload(
    *,
    device_type,
    mount_plan=DEFAULT_MOUNT_PLAN_ID,
    owner,
    plan=DEFAULT_PLAN_ID,
    request_object_id=DEFAULT_SIGNPOST_PLAN_ID,
    **kwargs,
) -> dict:
    result = {
        "id": request_object_id,
        "device_type": device_type,
        "mount_plan": mount_plan,
        "owner": owner,
        "plan": plan,
        "double_sided": True,
        "lifecycle": 3,
        "location": "SRID=3879;POINT Z (25496751.5 6673129.5 1.5)",
        "parent": None,
        "replaces": None,
        "seasonal_validity_period_information": "",
        "txt": "Example signpost plan for v1/plans/bulk-insert operation",
    }
    result.update(kwargs)
    return result


def traffic_sign_plan_payload(
    *,
    device_type,
    owner,
    location=POINT,
    mount_plan=DEFAULT_MOUNT_PLAN_ID,
    request_object_id=DEFAULT_TRAFFIC_SIGN_PLAN_ID,
    plan=DEFAULT_PLAN_ID,
    **kwargs,
) -> dict:
    result = {
        "id": request_object_id,
        "device_type": device_type,
        "mount_plan": mount_plan,
        "owner": owner,
        "plan": plan,
        "location": location,
        "double_sided": True,
        "lifecycle": 3,
        "peak_fastened": True,
        "seasonal_validity_period_information": "Winter constraints apply",
        "txt": "Example traffic sign plan for v1/plans/bulk-insert operation",
    }
    result.update(kwargs)
    return result


def _post_insert_plan_bulk(
    admin_client,
    *,
    additional_sign_plans=None,
    mount_plans=None,
    plan=None,
    signpost_plans=None,
    traffic_sign_plans=None,
):
    payload_obj = {}
    if additional_sign_plans:
        payload_obj["additional_sign_plans"] = additional_sign_plans
    if mount_plans:
        payload_obj["mount_plans"] = mount_plans
    if plan:
        payload_obj["plan"] = plan
    if signpost_plans:
        payload_obj["signpost_plans"] = signpost_plans
    if traffic_sign_plans:
        payload_obj["traffic_sign_plans"] = traffic_sign_plans
    payload = json.dumps(payload_obj, indent=2, default=str)

    return admin_client.post(reverse("v1:plan-bulk-insert"), data=payload, content_type="application/json")


@pytest.fixture
def owner():
    return OwnerFactory.create()


@pytest.fixture
def traffic_sign_device_type():
    return TrafficControlDeviceType.objects.create(
        code="123",
        description="Traffic Sign Test Device Type",
        target_model=DeviceTypeTargetModel.TRAFFIC_SIGN,
        value="12.3",
    )


@pytest.fixture
def additional_sign_device_type():
    return TrafficControlDeviceType.objects.create(
        code="234",
        description="Additional Sign Test Device Type",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        value="23.4",
    )


@pytest.fixture
def signpost_sign_device_type():
    return TrafficControlDeviceType.objects.create(
        code="345",
        description="SignPost Test Device Type",
        target_model=DeviceTypeTargetModel.SIGNPOST,
        value="34.5",
    )


@pytest.mark.django_db
def test_plan_bulk_insert_success(
    admin_client, additional_sign_device_type, signpost_sign_device_type, traffic_sign_device_type, owner
):
    # Sanity check that our objects do not exist yet in the database
    assert not AdditionalSignPlan.objects.filter(pk=DEFAULT_ADDITIONAL_SIGN_PLAN_ID).exists()
    assert not MountPlan.objects.filter(pk=DEFAULT_MOUNT_PLAN_ID).exists()
    assert not Plan.objects.filter(pk=DEFAULT_PLAN_ID).exists()
    assert not SignpostPlan.objects.filter(pk=DEFAULT_SIGNPOST_PLAN_ID).exists()
    assert not TrafficSignPlan.objects.filter(pk=DEFAULT_TRAFFIC_SIGN_PLAN_ID).exists()

    # Send a request with good objects for every category
    response = _post_insert_plan_bulk(
        admin_client,
        additional_sign_plans=[
            additional_sign_plan_payload(device_type=additional_sign_device_type.pk, owner=owner.pk)
        ],
        mount_plans=[mount_plan_payload(owner=owner.pk)],
        plan=plan_payload(),
        signpost_plans=[signpost_plan_payload(device_type=signpost_sign_device_type.pk, owner=owner.pk)],
        traffic_sign_plans=[traffic_sign_plan_payload(device_type=traffic_sign_device_type.pk, owner=owner.pk)],
    )

    # Basic response check
    response_data = response.json()
    assert response.status_code == status.HTTP_201_CREATED

    # Check that the returned objects are present in the response
    assert len(response_data.get("additional_sign_plans")) == 1, "Should create one additional sign plan"
    assert len(response_data.get("mount_plans")) == 1, "Should create one mount plan"
    assert "plan" in response_data, "Should include plan"
    assert len(response_data.get("signpost_plans")) == 1, "Should create one signpost plan"
    assert len(response_data.get("traffic_sign_plans")) == 1, "Should create one traffic sign plan"

    # Check that the returned objects have been created with the expected IDs
    assert response_data.get("additional_sign_plans")[0]["id"] == DEFAULT_ADDITIONAL_SIGN_PLAN_ID
    assert response_data.get("mount_plans")[0]["id"] == DEFAULT_MOUNT_PLAN_ID
    assert response_data.get("plan")["id"] == DEFAULT_PLAN_ID
    assert response_data.get("signpost_plans")[0]["id"] == DEFAULT_SIGNPOST_PLAN_ID
    assert response_data.get("traffic_sign_plans")[0]["id"] == DEFAULT_TRAFFIC_SIGN_PLAN_ID

    # Check that our objects got created in the database
    assert AdditionalSignPlan.objects.filter(pk=DEFAULT_ADDITIONAL_SIGN_PLAN_ID).exists()
    assert MountPlan.objects.filter(pk=DEFAULT_MOUNT_PLAN_ID).exists()
    assert Plan.objects.filter(pk=DEFAULT_PLAN_ID).exists()
    assert SignpostPlan.objects.filter(pk=DEFAULT_SIGNPOST_PLAN_ID).exists()
    assert TrafficSignPlan.objects.filter(pk=DEFAULT_TRAFFIC_SIGN_PLAN_ID).exists()


@pytest.mark.django_db
def test_plan_bulk_insert_is_atomic(
    admin_client, additional_sign_device_type, signpost_sign_device_type, traffic_sign_device_type, owner
):
    # Send a request with many good objects and a single error
    response = _post_insert_plan_bulk(
        admin_client,
        additional_sign_plans=[
            additional_sign_plan_payload(device_type=additional_sign_device_type.pk, owner=owner.pk)
        ],
        mount_plans=[mount_plan_payload(owner="bogus-id")],
        plan=plan_payload(),
        signpost_plans=[signpost_plan_payload(device_type=signpost_sign_device_type.pk, owner=owner.pk)],
        traffic_sign_plans=[traffic_sign_plan_payload(device_type=traffic_sign_device_type.pk, owner=owner.pk)],
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Check that none of our objects got created as a result
    assert not AdditionalSignPlan.objects.filter(pk=DEFAULT_ADDITIONAL_SIGN_PLAN_ID).exists()
    assert not MountPlan.objects.filter(pk=DEFAULT_MOUNT_PLAN_ID).exists()
    assert not Plan.objects.filter(pk=DEFAULT_PLAN_ID).exists()
    assert not SignpostPlan.objects.filter(pk=DEFAULT_SIGNPOST_PLAN_ID).exists()
    assert not TrafficSignPlan.objects.filter(pk=DEFAULT_TRAFFIC_SIGN_PLAN_ID).exists()


@pytest.mark.django_db
def test_plan_bulk_insert_single_object_validation_failure(admin_client, owner):
    # Send request with 1 bogus mount plan with single error and 1 OK plan
    response = _post_insert_plan_bulk(
        admin_client,
        mount_plans=[mount_plan_payload(owner="bogus-id"), mount_plan_payload(id=ALT_MOUNT_PLAN_ID, owner=owner.pk)],
        plan=plan_payload(),
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Assert that we only get a single complaint about mount plans and no other objects are mentioned in response
    assert "plan" not in response_data, "Should not complain about plan"
    assert len(response_data) == 1, "Response should not contain unexpected keys"
    assert len(response_data.get("mount_plans")) == 2, "Mount plan errors array should have same length as in input"
    assert "owner" in response_data["mount_plans"][0], "First mount plan complaint should be about the owner field"
    assert len(response_data.get("mount_plans")[0]) == 1, "Should have no other complaints about the first mount plan"
    assert not response_data.get("mount_plans")[1], "Second mount plan error list should be empty"


@pytest.mark.django_db
def test_plan_bulk_insert_multiple_object_validation_failures(admin_client, owner, traffic_sign_device_type):
    # Send request with 1 bogus mount plan, 3 traffic sign plans [BOGUS_X2, OK, BOGUS], and 1 OK plan
    response = _post_insert_plan_bulk(
        admin_client,
        mount_plans=[mount_plan_payload(owner="bogus-id")],
        plan=plan_payload(),
        traffic_sign_plans=[
            traffic_sign_plan_payload(device_type="bogus-device-type-id", owner="another-bogus-id"),  # two complaints
            traffic_sign_plan_payload(device_type=traffic_sign_device_type.pk, owner=owner.pk),  # no complaints
            traffic_sign_plan_payload(device_type="bogus-device-type-id", owner=owner.pk),  # one complaint
        ],
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Expect only categories with bogus elements to appear in response
    assert "mount_plans" in response_data, "Should complain about mount plans"
    assert "traffic_sign_plans" in response_data, "Should complain about traffic sign plans"
    assert len(response_data) == 2, "Response contains unexpected keys"

    # Expect a single complaint for mount plans
    assert len(response_data.get("mount_plans")) == 1, "Should have one mount plan complaint"
    assert "owner" in response_data["mount_plans"][0], "Complaint should be about the owner field"
    assert len(response_data.get("mount_plans")[0]) == 1, "Should have no other mount plan complaints"

    # Expect the correct error count per traffic sign plan
    assert len(response_data.get("traffic_sign_plans")) == 3, "Should have three traffic sign plan entries"
    assert len(response_data.get("traffic_sign_plans")[0]) == 2, "First traffic sign plan should have two complaints"
    assert len(response_data.get("traffic_sign_plans")[1]) == 0, "Second traffic sign plan should have no complaints"
    assert len(response_data.get("traffic_sign_plans")[2]) == 1, "Third traffic sign plan should have one complaint"

    # Expect every bogus field to be indicated for each bogus mount plan
    assert "owner" in response_data.get("traffic_sign_plans")[0], "First plan missing owner complaint"
    assert "device_type" in response_data.get("traffic_sign_plans")[0], "First plan missing device type complaint"
    assert "device_type" in response_data.get("traffic_sign_plans")[2], "Third plan missing device type complaint"


@pytest.mark.django_db
def test_plan_bulk_insert_cycle_detected_failure(admin_client, owner, signpost_sign_device_type):
    # Assign both signposts' parent field to each other
    response = _post_insert_plan_bulk(
        admin_client,
        plan=plan_payload(),
        signpost_plans=[
            signpost_plan_payload(
                device_type=signpost_sign_device_type.pk,
                owner=owner.pk,
                parent=ALT_SIGNPOST_PLAN_ID,
                request_object_id=DEFAULT_SIGNPOST_PLAN_ID,
            ),
            signpost_plan_payload(
                device_type=signpost_sign_device_type.pk,
                owner=owner.pk,
                parent=DEFAULT_SIGNPOST_PLAN_ID,
                request_object_id=ALT_SIGNPOST_PLAN_ID,
            ),
        ],
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Expect error about dependency cycle between objects
    assert NON_FIELD_ERRORS in response_data, "Response should have non-field errors"
    assert len(response_data) == 1, "Response contains unexpected keys"
    assert len(response_data.get(NON_FIELD_ERRORS)) == 1, "Response should have only one non-field error"

    cycle_error = response_data.get(NON_FIELD_ERRORS)[0]
    assert "nodes are in a cycle" in cycle_error, "Error should be about dependency cycle"

    # Expect circular dependency objects to have their IDs accused
    assert DEFAULT_SIGNPOST_PLAN_ID in cycle_error, "Should accuse elements with loop"
    assert ALT_SIGNPOST_PLAN_ID in cycle_error, "Should accuse elements with loop"


@pytest.mark.django_db
def test_plan_bulk_insert_rejects_object_duplication(admin_client):  # (or database-level complaints in general)
    # Pre-create an object
    PlanFactory.create(id=DEFAULT_PLAN_ID)

    # Attempt to create the object with the endpoint
    response = _post_insert_plan_bulk(
        admin_client,
        plan=plan_payload(request_object_id=DEFAULT_PLAN_ID),
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Expect duplicate plan object complaint
    assert "plan" in response_data, "Should complain about plan"
    assert len(response_data) == 1, "Response contains unexpected keys"
    assert NON_FIELD_ERRORS in response_data.get("plan"), "Complaint should be about non field errors"
    assert len(response_data.get("plan")[NON_FIELD_ERRORS]) == 1, "Response should have only one non field error"
    duplication_error = response_data.get("plan")[NON_FIELD_ERRORS][0]
    assert "duplicate" in duplication_error, "Complaint should mention 'duplicate'"


@pytest.mark.django_db
def test_plan_bulk_insert_announces_cascading_errors_neatly(admin_client, owner):
    # Ensure the plan creation will fail, assign the failing plan to two otherwise properly defined mount plans
    PlanFactory.create(id=DEFAULT_PLAN_ID)
    response = _post_insert_plan_bulk(
        admin_client,
        mount_plans=[
            mount_plan_payload(owner=owner.pk),
            mount_plan_payload(owner=owner.pk, request_object_id=ALT_MOUNT_PLAN_ID),
        ],
        plan=plan_payload(request_object_id=DEFAULT_PLAN_ID),
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Expect both mount plans to fail
    assert "plan" in response_data, "Should complain about plan"
    assert "mount_plans" in response_data, "Should complain about mount plans"
    assert len(response_data) == 2, "Response contains unexpected keys"

    # Both mount plans should explain they could not be created because the plan was not created
    mount_plan_errors = response_data.get("mount_plans")
    assert len(mount_plan_errors) == 2, "Both mount plans should fail"
    assert f"Dependency plan ({DEFAULT_PLAN_ID}) was not created by this request." in mount_plan_errors[0]["plan"]
    assert f"Dependency plan ({DEFAULT_PLAN_ID}) was not created by this request." in mount_plan_errors[1]["plan"]


@pytest.mark.django_db
def test_plan_bulk_insert_replaces_stuff_properly(
    admin_client, additional_sign_device_type, signpost_sign_device_type, traffic_sign_device_type, owner
):
    old_plan = PlanFactory.create()
    old_mount = MountPlanFactory.create(plan=old_plan)
    old_signpost = SignpostPlanFactory.create(plan=old_plan, mount_plan=old_mount)
    old_trafficsign = TrafficSignPlanFactory.create(plan=old_plan, mount_plan=old_mount)
    old_additionalsign = AdditionalSignPlanFactory.create(
        plan=old_plan, mount_plan=old_mount, signpost_plan=old_signpost, parent=old_trafficsign
    )

    assert old_mount.replaced_by is None
    assert old_signpost.replaced_by is None
    assert old_trafficsign.replaced_by is None
    assert old_additionalsign.replaced_by is None

    _post_insert_plan_bulk(
        admin_client,
        plan=plan_payload(owner=owner.pk, replaces=old_plan.pk),
        mount_plans=[mount_plan_payload(owner=owner.pk, replaces=old_mount.pk)],
        signpost_plans=[
            signpost_plan_payload(owner=owner.pk, replaces=old_signpost.pk, device_type=signpost_sign_device_type.pk)
        ],
        traffic_sign_plans=[
            traffic_sign_plan_payload(
                owner=owner.pk, replaces=old_trafficsign.pk, device_type=traffic_sign_device_type.pk
            )
        ],
        additional_sign_plans=[
            additional_sign_plan_payload(
                owner=owner.pk, replaces=old_additionalsign.pk, device_type=additional_sign_device_type.pk
            )
        ],
    )

    old_mount.refresh_from_db()
    old_signpost.refresh_from_db()
    old_trafficsign.refresh_from_db()
    old_additionalsign.refresh_from_db()

    assert old_mount.is_replaced and str(old_mount.replaced_by.pk) == DEFAULT_MOUNT_PLAN_ID
    assert old_signpost.is_replaced and str(old_signpost.replaced_by.pk) == DEFAULT_SIGNPOST_PLAN_ID
    assert old_trafficsign.is_replaced and str(old_trafficsign.replaced_by.pk) == DEFAULT_TRAFFIC_SIGN_PLAN_ID
    assert old_additionalsign.is_replaced and str(old_additionalsign.replaced_by.pk) == DEFAULT_ADDITIONAL_SIGN_PLAN_ID


@pytest.mark.django_db
def test_plan_bulk_insert_expects_new_objects(
    admin_client, additional_sign_device_type, signpost_sign_device_type, traffic_sign_device_type, owner
):
    old_plan = PlanFactory.create()
    old_mount = MountPlanFactory.create()

    response = _post_insert_plan_bulk(
        admin_client,
        plan=plan_payload(owner=owner.pk),
        mount_plans=[mount_plan_payload(owner=owner.pk, plan=old_plan.pk)],
        signpost_plans=[
            signpost_plan_payload(owner=owner.pk, mount_plan=old_mount.pk, device_type=signpost_sign_device_type.pk),
            signpost_plan_payload(
                id=ALT_MOUNT_PLAN_ID,
                owner=owner.pk,
                plan=NON_EXISTENT_ID,
                mount_plan=NON_EXISTENT_ID,
                device_type=signpost_sign_device_type.pk,
            ),
        ],
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "mount_plans" in response_data
    assert "signpost_plans" in response_data

    # References to pre-existing plans fail
    mount_plan_errors = response_data.get("mount_plans")
    assert "plan" in mount_plan_errors[0]
    assert f"Dependency plan ({old_plan.id}) was not created by this request." in mount_plan_errors[0]["plan"]

    # References to pre-existing device plans fail in the same manner
    signpost_plan_errors = response_data.get("signpost_plans")
    assert "mount_plan" in signpost_plan_errors[0]
    assert (
        f"Dependency mount_plan ({old_mount.id}) was not created by this request."
        in signpost_plan_errors[0]["mount_plan"]
    )

    # References to non_existing device plans fail in the same manner
    assert "mount_plan" in signpost_plan_errors[1]
    assert (
        f"Dependency mount_plan ({NON_EXISTENT_ID}) was not created by this request."
        in signpost_plan_errors[1]["mount_plan"]
    )

    # Multiple missing references in the same object will result in multiple complaints
    assert len(signpost_plan_errors[1]) == 2
    assert "plan" in signpost_plan_errors[1]
    assert f"Dependency plan ({NON_EXISTENT_ID}) was not created by this request." in signpost_plan_errors[1]["plan"]
