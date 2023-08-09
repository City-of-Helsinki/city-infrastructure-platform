import uuid

import pytest
from django.urls import reverse

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.tests.factories import (
    get_additional_sign_plan,
    get_additional_sign_real,
    get_mount_plan,
    get_mount_real,
    get_traffic_control_device_type,
    get_traffic_sign_plan,
    get_traffic_sign_real,
)


@pytest.mark.parametrize(
    ("ts_factory", "as_factory", "mount_factory", "mount_parameter", "url_name"),
    (
        (get_traffic_sign_plan, get_additional_sign_plan, get_mount_plan, "mount_plan", "traffic-sign-plan-embed"),
        (get_traffic_sign_real, get_additional_sign_real, get_mount_real, "mount_real", "traffic-sign-real-embed"),
    ),
)
@pytest.mark.parametrize("has_device_type", (False, True))
@pytest.mark.parametrize("has_additional_signs", (False, True))
@pytest.mark.parametrize("has_additional_sign_device_types", (False, True))
@pytest.mark.parametrize("has_mount", (False, True))
@pytest.mark.django_db
def test__embed__traffic_sign__context(
    settings,
    client,
    ts_factory,
    as_factory,
    mount_factory,
    mount_parameter,
    url_name,
    has_device_type,
    has_additional_signs,
    has_additional_sign_device_types,
    has_mount,
):
    """Test that the embedded view can be built and its context has the objects that it should."""

    settings.STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

    if has_mount:
        mount = mount_factory()
    else:
        mount = None

    if has_device_type:
        traffic_sign_type = get_traffic_control_device_type(
            code="TS1",
            target_model=DeviceTypeTargetModel.TRAFFIC_SIGN,
        )
    else:
        traffic_sign_type = None

    traffic_sign = ts_factory(device_type=traffic_sign_type, **{mount_parameter: mount})

    if has_additional_signs:
        if has_additional_sign_device_types:
            additional_sign_type_1 = get_traffic_control_device_type(
                code="AS1",
                target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
            )
            additional_sign_type_2 = get_traffic_control_device_type(
                code="AS2",
                target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
            )
        else:
            additional_sign_type_1 = None
            additional_sign_type_2 = None

        additional_sign_1 = as_factory(
            device_type=additional_sign_type_1,
            parent=traffic_sign,
            order=1,
            **{mount_parameter: mount},
        )
        additional_sign_2 = as_factory(
            device_type=additional_sign_type_2,
            parent=traffic_sign,
            order=2,
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

    if has_device_type:
        assert context.get("traffic_sign_fields")[0][1] == traffic_sign_type.code
    else:
        assert context.get("traffic_sign_fields")[0][1] is None

    if has_additional_signs:
        assert len(context.get("additional_signs")) == 2

        assert context.get("additional_signs")[0]["object"] == additional_sign_1
        assert context.get("additional_signs")[0]["fields"][3][1] == additional_sign_1.id

        assert context.get("additional_signs")[1]["object"] == additional_sign_2
        assert context.get("additional_signs")[1]["fields"][3][1] == additional_sign_2.id

        if has_additional_sign_device_types:
            assert context.get("additional_signs")[0]["fields"][0][1] == additional_sign_type_1.code
            assert context.get("additional_signs")[1]["fields"][0][1] == additional_sign_type_2.code
        else:
            assert context.get("additional_signs")[0]["fields"][0][1] is None
            assert context.get("additional_signs")[1]["fields"][0][1] is None
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
