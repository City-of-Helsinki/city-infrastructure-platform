import pytest
from django.urls import reverse
from guardian.shortcuts import assign_perm

from traffic_control.tests.factories import BarrierPlanFactory, BarrierPlanFileFactory, UserFactory


@pytest.mark.django_db
def test__health_check(client, settings):
    env_name = "envname"
    version = "abc123"
    settings.ENVIRONMENT_NAME = env_name
    settings.VERSION = version

    url = reverse("health-check")
    response = client.get(url)
    response_json = response.json()

    assert response.status_code == 200
    assert response_json.get("status") == "OK"
    assert response_json.get("service") == "city-infrastructure-platform"
    assert response_json.get("environment") == env_name
    assert response_json.get("version") == version


@pytest.mark.parametrize("is_public", [False, True])
@pytest.mark.parametrize("has_table_permission", [False, True])
@pytest.mark.parametrize("has_object_permission", [False, True])
@pytest.mark.django_db
def test__file_proxy_view_authenticated_user(
    client,
    is_public,
    has_table_permission,
    has_object_permission,
):
    user = UserFactory()
    barrier_plan = BarrierPlanFactory()
    file = BarrierPlanFileFactory(barrier_plan=barrier_plan, is_public=is_public, file__data=b"Barrier plan file data")
    url = reverse(
        "planfiles_proxy",
        kwargs={
            "model_name": "barrier",
            "file_id": file.file.name.split("/")[-1],
        },
    )

    if has_table_permission:
        assign_perm("traffic_control.view_barrierplanfile", user)
        user.refresh_from_db()

    if has_object_permission:
        assign_perm("traffic_control.view_barrierplanfile", user, file)
        user.refresh_from_db()

    client.force_login(user)
    response = client.get(url)
    if is_public or has_table_permission or has_object_permission:
        assert response.status_code == 200
        assert b"".join(response.streaming_content) == b"Barrier plan file data"
    else:
        assert response.status_code == 403


@pytest.mark.parametrize("is_public", [False, True])
@pytest.mark.django_db
def test__file_proxy_view_anonymous_user(client, is_public):
    """
    Tests that an anonymous (unauthenticated) user can access
    public files but not private files.
    """
    barrier_plan = BarrierPlanFactory()
    file = BarrierPlanFileFactory(barrier_plan=barrier_plan, is_public=is_public, file__data=b"Some content")
    url = reverse(
        "planfiles_proxy",
        kwargs={
            "model_name": "barrier",
            "file_id": file.file.name.split("/")[-1],
        },
    )

    response = client.get(url)
    if is_public:
        assert response.status_code == 200
        assert b"".join(response.streaming_content) == b"Some content"
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test__file_proxy_view_bogus_file(client):
    """
    Tests that the file proxy view returns 404 for non-existent files
    """
    url = reverse(
        "planfiles_proxy",
        kwargs={
            "model_name": "barrier",
            "file_id": "bogus.txt",
        },
    )

    response = client.get(url)
    assert response.status_code == 404
