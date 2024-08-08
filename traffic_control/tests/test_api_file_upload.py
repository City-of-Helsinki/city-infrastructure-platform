import io
import shutil
import tempfile
import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail

from traffic_control.models import (
    BarrierPlan,
    BarrierPlanFile,
    BarrierReal,
    BarrierRealFile,
    MountPlan,
    MountPlanFile,
    MountReal,
    MountRealFile,
    RoadMarkingPlan,
    RoadMarkingPlanFile,
    RoadMarkingReal,
    RoadMarkingRealFile,
    SignpostPlan,
    SignpostPlanFile,
    SignpostReal,
    SignpostRealFile,
    TrafficLightPlan,
    TrafficLightPlanFile,
    TrafficLightReal,
    TrafficLightRealFile,
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignReal,
    TrafficSignRealFile,
)
from traffic_control.tests.factories import (
    get_api_client,
    get_barrier_plan,
    get_barrier_real,
    get_mount_plan,
    get_mount_real,
    get_road_marking_plan,
    get_road_marking_real,
    get_signpost_plan,
    get_signpost_real,
    get_traffic_light_plan,
    get_traffic_light_real,
    get_traffic_sign_plan,
    get_traffic_sign_real,
    get_user,
)

MEDIA_ROOT = tempfile.mkdtemp()

settings_overrides = override_settings(MEDIA_ROOT=MEDIA_ROOT)


DELETE_TEST_PARAMS = (
    (get_barrier_plan, BarrierPlan, BarrierPlanFile, "barrier_plan", "barrierplan"),
    (get_barrier_real, BarrierReal, BarrierRealFile, "barrier_real", "barrierreal"),
    (get_mount_plan, MountPlan, MountPlanFile, "mount_plan", "mountplan"),
    (get_mount_real, MountReal, MountRealFile, "mount_real", "mountreal"),
    (
        get_road_marking_plan,
        RoadMarkingPlan,
        RoadMarkingPlanFile,
        "road_marking_plan",
        "roadmarkingplan",
    ),
    (
        get_road_marking_real,
        RoadMarkingReal,
        RoadMarkingRealFile,
        "road_marking_real",
        "roadmarkingreal",
    ),
    (
        get_signpost_plan,
        SignpostPlan,
        SignpostPlanFile,
        "signpost_plan",
        "signpostplan",
    ),
    (
        get_signpost_real,
        SignpostReal,
        SignpostRealFile,
        "signpost_real",
        "signpostreal",
    ),
    (
        get_traffic_light_plan,
        TrafficLightPlan,
        TrafficLightPlanFile,
        "traffic_light_plan",
        "trafficlightplan",
    ),
    (
        get_traffic_light_real,
        TrafficLightReal,
        TrafficLightRealFile,
        "traffic_light_real",
        "trafficlightreal",
    ),
    (
        get_traffic_sign_plan,
        TrafficSignPlan,
        TrafficSignPlanFile,
        "traffic_sign_plan",
        "trafficsignplan",
    ),
    (
        get_traffic_sign_real,
        TrafficSignReal,
        TrafficSignRealFile,
        "traffic_sign_real",
        "trafficsignreal",
    ),
)


def setup_module():
    settings_overrides.enable()


def teardown_module():
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
    settings_overrides.disable()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory,model_class,url_name",
    (
        (get_barrier_plan, BarrierPlan, "barrierplan"),
        (get_barrier_real, BarrierReal, "barrierreal"),
        (get_mount_plan, MountPlan, "mountplan"),
        (get_mount_real, MountReal, "mountreal"),
        (get_road_marking_plan, RoadMarkingPlan, "roadmarkingplan"),
        (get_road_marking_real, RoadMarkingReal, "roadmarkingreal"),
        (get_signpost_plan, SignpostPlan, "signpostplan"),
        (get_signpost_real, SignpostReal, "signpostreal"),
        (get_traffic_light_plan, TrafficLightPlan, "trafficlightplan"),
        (get_traffic_light_real, TrafficLightReal, "trafficlightreal"),
        (get_traffic_sign_plan, TrafficSignPlan, "trafficsignplan"),
        (get_traffic_sign_real, TrafficSignReal, "trafficsignreal"),
    ),
)
def test_file_upload(factory, model_class, url_name):
    user = get_user("test_superuser", admin=True)
    api_client = get_api_client(user)
    obj = factory()

    post_response = api_client.post(
        reverse(f"v1:{url_name}-post-files", kwargs={"pk": obj.pk}),
        data={
            "file1": io.BytesIO(b"File 1 contents"),
            "file2": io.BytesIO(b"File 2 contents"),
        },
        format="multipart",
    )

    obj.refresh_from_db()
    assert post_response.status_code == status.HTTP_200_OK
    assert model_class.objects.count() == 1
    assert obj.files.count() == 2
    with open(obj.files.get(file__endswith="file1").file.path, "r") as f:
        assert f.read() == "File 1 contents"
    with open(obj.files.get(file__endswith="file2").file.path, "r") as f:
        assert f.read() == "File 2 contents"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory,model_class,url_name",
    (
        (get_barrier_plan, BarrierPlan, "barrierplan"),
        (get_barrier_real, BarrierReal, "barrierreal"),
        (get_mount_plan, MountPlan, "mountplan"),
        (get_mount_real, MountReal, "mountreal"),
        (get_road_marking_plan, RoadMarkingPlan, "roadmarkingplan"),
        (get_road_marking_real, RoadMarkingReal, "roadmarkingreal"),
        (get_signpost_plan, SignpostPlan, "signpostplan"),
        (get_signpost_real, SignpostReal, "signpostreal"),
        (get_traffic_light_plan, TrafficLightPlan, "trafficlightplan"),
        (get_traffic_light_real, TrafficLightReal, "trafficlightreal"),
        (get_traffic_sign_plan, TrafficSignPlan, "trafficsignplan"),
        (get_traffic_sign_real, TrafficSignReal, "trafficsignreal"),
    ),
)
def test_invalid_file_upload(factory, model_class, url_name):
    user = get_user("test_superuser", admin=True)
    api_client = get_api_client(user)
    obj = factory()

    post_response = api_client.post(
        reverse(f"v1:{url_name}-post-files", kwargs={"pk": obj.pk}),
        data={"file1": io.BytesIO(b"File contents"), "file2": "This is not a file"},
        format="multipart",
    )

    obj.refresh_from_db()
    assert post_response.status_code == status.HTTP_400_BAD_REQUEST
    assert model_class.objects.count() == 1
    assert obj.files.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory,model_class,file_model_class,related_name,url_name",
    (
        (get_barrier_plan, BarrierPlan, BarrierPlanFile, "barrier_plan", "barrierplan"),
        (get_barrier_real, BarrierReal, BarrierRealFile, "barrier_real", "barrierreal"),
        (get_mount_plan, MountPlan, MountPlanFile, "mount_plan", "mountplan"),
        (get_mount_real, MountReal, MountRealFile, "mount_real", "mountreal"),
        (
            get_road_marking_plan,
            RoadMarkingPlan,
            RoadMarkingPlanFile,
            "road_marking_plan",
            "roadmarkingplan",
        ),
        (
            get_road_marking_real,
            RoadMarkingReal,
            RoadMarkingRealFile,
            "road_marking_real",
            "roadmarkingreal",
        ),
        (
            get_signpost_plan,
            SignpostPlan,
            SignpostPlanFile,
            "signpost_plan",
            "signpostplan",
        ),
        (
            get_signpost_real,
            SignpostReal,
            SignpostRealFile,
            "signpost_real",
            "signpostreal",
        ),
        (
            get_traffic_light_plan,
            TrafficLightPlan,
            TrafficLightPlanFile,
            "traffic_light_plan",
            "trafficlightplan",
        ),
        (
            get_traffic_light_real,
            TrafficLightReal,
            TrafficLightRealFile,
            "traffic_light_real",
            "trafficlightreal",
        ),
        (
            get_traffic_sign_plan,
            TrafficSignPlan,
            TrafficSignPlanFile,
            "traffic_sign_plan",
            "trafficsignplan",
        ),
        (
            get_traffic_sign_real,
            TrafficSignReal,
            TrafficSignRealFile,
            "traffic_sign_real",
            "trafficsignreal",
        ),
    ),
)
def test_file_rewrite(factory, model_class, file_model_class, related_name, url_name):
    user = get_user("test_superuser", admin=True)
    api_client = get_api_client(user)
    obj = factory()
    file_obj = file_model_class.objects.create(
        **{
            related_name: obj,
            "file": SimpleUploadedFile("temp.txt", b"File contents"),
        },
    )

    patch_response = api_client.patch(
        reverse(
            f"v1:{url_name}-change-file",
            kwargs={"pk": obj.id, "file_pk": file_obj.id},
        ),
        data={"file": io.BytesIO(b"Rewritten file contents")},
        format="multipart",
    )

    obj.refresh_from_db()
    file_obj.refresh_from_db()
    assert patch_response.status_code == status.HTTP_200_OK
    assert model_class.objects.count() == 1
    assert obj.files.count() == 1
    with open(file_obj.file.path, "r") as f:
        assert f.read() == "Rewritten file contents"


@pytest.mark.django_db
@pytest.mark.parametrize("factory,model_class,file_model_class,related_name,url_name", DELETE_TEST_PARAMS)
def test_file_delete(factory, model_class, file_model_class, related_name, url_name):
    user = get_user("test_superuser", admin=True)
    api_client = get_api_client(user)
    obj = factory()
    file_obj = file_model_class.objects.create(
        **{
            related_name: obj,
            "file": SimpleUploadedFile("temp.txt", b"File contents"),
        },
    )

    delete_response = api_client.delete(
        reverse(
            f"v1:{url_name}-change-file",
            kwargs={"pk": obj.id, "file_pk": file_obj.id},
        ),
    )

    obj.refresh_from_db()
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert model_class.objects.count() == 1
    assert obj.files.count() == 0
    assert not file_model_class.objects.filter(pk=file_obj.pk).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("factory,model_class,file_model_class,related_name,url_name", DELETE_TEST_PARAMS)
def test_file_delete_with_non_existing_base_object(factory, model_class, file_model_class, related_name, url_name):
    user = get_user("test_superuser", admin=True)
    api_client = get_api_client(user)
    obj = factory()
    non_existing_uuid = uuid.uuid4()
    file_obj = file_model_class.objects.create(
        **{
            related_name: obj,
            "file": SimpleUploadedFile("temp.txt", b"File contents"),
        },
    )

    delete_response = api_client.delete(
        reverse(
            f"v1:{url_name}-change-file",
            kwargs={"pk": non_existing_uuid, "file_pk": file_obj.id},
        ),
    )

    obj.refresh_from_db()
    expected_error_detail = ErrorDetail(
        string=f"No {model_class._meta.object_name} matches the given query.", code="not_found"
    )
    assert delete_response.status_code == status.HTTP_404_NOT_FOUND
    assert delete_response.data.get("detail") == expected_error_detail
    assert model_class.objects.count() == 1
    assert obj.files.count() == 1
    assert file_model_class.objects.filter(pk=file_obj.pk).exists()


@pytest.mark.parametrize(
    "factory, model_class, file_model_class, related_name, url_name",
    (
        (
            get_barrier_plan,
            BarrierPlan,
            BarrierPlanFile,
            "barrier_plan",
            "barrierplan",
        ),
        (
            get_barrier_real,
            BarrierReal,
            BarrierRealFile,
            "barrier_real",
            "barrierreal",
        ),
        (
            get_mount_plan,
            MountPlan,
            MountPlanFile,
            "mount_plan",
            "mountplan",
        ),
        (
            get_mount_real,
            MountReal,
            MountRealFile,
            "mount_real",
            "mountreal",
        ),
        (
            get_road_marking_plan,
            RoadMarkingPlan,
            RoadMarkingPlanFile,
            "road_marking_plan",
            "roadmarkingplan",
        ),
        (
            get_road_marking_real,
            RoadMarkingReal,
            RoadMarkingRealFile,
            "road_marking_real",
            "roadmarkingreal",
        ),
        (
            get_signpost_plan,
            SignpostPlan,
            SignpostPlanFile,
            "signpost_plan",
            "signpostplan",
        ),
        (
            get_signpost_real,
            SignpostReal,
            SignpostRealFile,
            "signpost_real",
            "signpostreal",
        ),
        (
            get_traffic_light_plan,
            TrafficLightPlan,
            TrafficLightPlanFile,
            "traffic_light_plan",
            "trafficlightplan",
        ),
        (
            get_traffic_light_real,
            TrafficLightReal,
            TrafficLightRealFile,
            "traffic_light_real",
            "trafficlightreal",
        ),
        (
            get_traffic_sign_plan,
            TrafficSignPlan,
            TrafficSignPlanFile,
            "traffic_sign_plan",
            "trafficsignplan",
        ),
        (
            get_traffic_sign_real,
            TrafficSignReal,
            TrafficSignRealFile,
            "traffic_sign_real",
            "trafficsignreal",
        ),
    ),
)
@pytest.mark.parametrize(
    "method, view_type, expected_status",
    (
        ("OPTIONS", "change-file", status.HTTP_200_OK),
        ("OPTIONS", "post-files", status.HTTP_200_OK),
        ("GET", "change-file", status.HTTP_405_METHOD_NOT_ALLOWED),
        ("GET", "post-files", status.HTTP_405_METHOD_NOT_ALLOWED),
        ("HEAD", "change-file", status.HTTP_405_METHOD_NOT_ALLOWED),
        ("HEAD", "post-files", status.HTTP_405_METHOD_NOT_ALLOWED),
        ("POST", "change-file", status.HTTP_401_UNAUTHORIZED),
        ("POST", "post-files", status.HTTP_401_UNAUTHORIZED),
        ("PUT", "change-file", status.HTTP_401_UNAUTHORIZED),
        ("PUT", "post-files", status.HTTP_401_UNAUTHORIZED),
        ("PATCH", "change-file", status.HTTP_401_UNAUTHORIZED),
        ("PATCH", "post-files", status.HTTP_401_UNAUTHORIZED),
        ("DELETE", "change-file", status.HTTP_401_UNAUTHORIZED),
        ("DELETE", "post-files", status.HTTP_401_UNAUTHORIZED),
    ),
)
@pytest.mark.django_db
def test__file_operations_by_anonymous_user(
    method,
    view_type,
    expected_status,
    factory,
    model_class,
    file_model_class,
    related_name,
    url_name,
):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    obj = factory()
    file_obj = file_model_class.objects.create(
        **{
            related_name: obj,
            "file": SimpleUploadedFile("temp.txt", b"File contents"),
        },
    )
    kwargs = {"pk": obj.id}
    if view_type == "change-file":
        kwargs["file_pk"] = file_obj.id

    resource_path = reverse(f"v1:{url_name}-{view_type}", kwargs=kwargs)

    response = client.generic(method, resource_path)

    obj.refresh_from_db()
    assert response.status_code == expected_status
    assert model_class.objects.count() == 1
    assert obj.files.count() == 1
    assert file_model_class.objects.filter(pk=file_obj.pk).exists()
