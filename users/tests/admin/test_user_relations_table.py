import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils.html import escape

User = get_user_model()

settings_overrides = override_settings(
    STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
)


def setup_module():
    settings_overrides.enable()


def teardown_module():
    settings_overrides.disable()


@pytest.fixture
def target_user(db):
    return User.objects.create(username="target_user")


def test_user_change_page_renders_relations_table(admin_client, target_user):
    """
    Verify that the user admin change page renders the relations table
    with correctly formatted URLs and query parameters.
    """
    change_page_url = reverse("admin:users_user_change", args=[target_user.pk])
    response = admin_client.get(change_page_url)

    assert response.status_code == 200

    html = response.content.decode("utf-8")

    # Check a standard 'created_by' link
    expected_ts_url = reverse("admin:traffic_control_trafficsignreal_changelist", query={"created_by": target_user.pk})
    assert escape(expected_ts_url) in html

    # Check the special 'deleted_by' link includes soft_deleted=1
    expected_barrier_url = reverse(
        "admin:traffic_control_barrierreal_changelist", query={"deleted_by": target_user.pk, "soft_deleted": "1"}
    )
    assert escape(expected_barrier_url) in html
