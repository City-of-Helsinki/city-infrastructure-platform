import uuid

import pytest
from django.urls import reverse

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    MountPlanFactory,
    MountRealFactory,
    TrafficControlDeviceTypeFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)


@pytest.mark.parametrize(
    ("ts_factory", "as_factory", "mount_factory", "mount_parameter", "url_name"),
    (
        (TrafficSignPlanFactory, AdditionalSignPlanFactory, MountPlanFactory, "mount_plan", "traffic-sign-plan-embed"),
        (TrafficSignRealFactory, AdditionalSignRealFactory, MountRealFactory, "mount_real", "traffic-sign-real-embed"),
    ),
)
@pytest.mark.parametrize("has_additional_signs", (False, True))
@pytest.mark.parametrize("has_mount", (False, True))
@pytest.mark.django_db
def test__embed__traffic_sign__context(
    client,
    ts_factory,
    as_factory,
    mount_factory,
    mount_parameter,
    url_name,
    has_additional_signs,
    has_mount,
):
    """Test that the embedded view can be built and its context has the objects that it should."""

    if has_mount:
        mount = mount_factory()
    else:
        mount = None

    traffic_sign_type = TrafficControlDeviceTypeFactory(
        code="TS1",
        target_model=DeviceTypeTargetModel.TRAFFIC_SIGN,
    )

    traffic_sign = ts_factory(device_type=traffic_sign_type, **{mount_parameter: mount})

    if has_additional_signs:
        additional_sign_type_1 = TrafficControlDeviceTypeFactory(
            code="AS1",
            target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        )
        additional_sign_type_2 = TrafficControlDeviceTypeFactory(
            code="AS2",
            target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        )
        additional_sign_1 = as_factory(
            device_type=additional_sign_type_1,
            parent=traffic_sign,
            height=2,
            **{mount_parameter: mount},
        )
        additional_sign_2 = as_factory(
            device_type=additional_sign_type_2,
            parent=traffic_sign,
            height=1,
            **{mount_parameter: mount},
        )
    else:
        additional_sign_1 = None
        additional_sign_2 = None

    response = client.get(reverse(url_name, kwargs={"pk": traffic_sign.id}))
    assert response.status_code == 200
    # Must not deny frame-embedding embedded views
    assert response.headers.get("x-frame-options") != "DENY"

    context = response.context
    assert context.get("object") == traffic_sign
    assert context.get("traffic_sign_fields")[3][1] == traffic_sign.id

    assert context.get("traffic_sign_fields")[0][1] == traffic_sign_type.code

    if has_additional_signs:
        assert len(context.get("additional_signs")) == 2

        assert context.get("additional_signs")[0]["object"] == additional_sign_1
        assert context.get("additional_signs")[0]["fields"][3][1] == additional_sign_1.id

        assert context.get("additional_signs")[1]["object"] == additional_sign_2
        assert context.get("additional_signs")[1]["fields"][3][1] == additional_sign_2.id

        assert context.get("additional_signs")[0]["fields"][0][1] == additional_sign_type_1.code
        assert context.get("additional_signs")[1]["fields"][0][1] == additional_sign_type_2.code
    else:
        assert context.get("additional_signs") == []

    if has_mount:
        assert context.get("mount_fields")[0][1] == mount.mount_type.code
        assert context.get("mount_fields")[5][1] == mount.id
    else:
        assert context.get("mount_fields") == []


@pytest.mark.parametrize("url_name", ("traffic-sign-plan-embed", "traffic-sign-real-embed"))
@pytest.mark.django_db
def test__embed__traffic_sign__not_found(client, url_name):
    """Test that the embedded view returns 404 when the object is not found."""
    response = client.get(reverse(url_name, kwargs={"pk": uuid.uuid4()}))
    assert response.status_code == 404
