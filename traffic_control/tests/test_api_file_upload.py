import io
import shutil
import tempfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

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
