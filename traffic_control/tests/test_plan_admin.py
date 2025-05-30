import pytest
from auditlog.models import LogEntry
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import MultiPolygon
from django.test import override_settings
from django.urls import reverse

from city_furniture.tests.factories import get_furniture_signpost_plan
from traffic_control.forms import PlanModelForm
from traffic_control.geometry_utils import get_z_for_polygon
from traffic_control.models import Plan
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    get_barrier_plan,
    get_mount_plan,
    get_plan,
    get_road_marking_plan,
    get_signpost_plan,
    get_traffic_light_plan,
    get_traffic_sign_plan,
    get_user,
    PlanFactory,
)
from traffic_control.tests.test_base_api import (
    illegal_multipolygon,
    invalid_ewkt_str,
    test_multi_polygon,
    test_point,
    test_point_2,
    test_polygon,
    test_polygon_2,
)
from traffic_control.tests.test_base_api_3d import test_point_2_3d, test_point_3d

settings_overrides = override_settings(
    STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
)


def setup_module():
    settings_overrides.enable()


def teardown_module():
    settings_overrides.disable()


@pytest.mark.django_db
def test_plan_relation_admin_view_requires_view_permission(client):
    user = get_user()
    get_user_model().objects.filter(pk=user.pk).update(is_staff=True)
    plan = get_plan()
    client.force_login(user)

    response = client.get(reverse("admin:traffic_control_plan_set-plans", kwargs={"object_id": plan.pk}))
    assert response.status_code == 403

    ct = ContentType.objects.get_for_model(Plan)
    view_perm = Permission.objects.get(codename="view_plan", content_type=ct)
    user.user_permissions.add(view_perm)
    response = client.get(reverse("admin:traffic_control_plan_set-plans", kwargs={"object_id": plan.pk}))
    assert response.status_code == 200


@pytest.mark.django_db
def test_plan_relation_admin_view_requires_change_permission(client):
    user = get_user()
    get_user_model().objects.filter(pk=user.pk).update(is_staff=True)
    client.force_login(user)
    ct = ContentType.objects.get_for_model(Plan)
    view_perm = Permission.objects.get(codename="view_plan", content_type=ct)
    user.user_permissions.add(view_perm)
    plan = get_plan()
    barrier_plan = get_barrier_plan()

    response = client.post(
        reverse("admin:traffic_control_plan_set-plans", kwargs={"object_id": plan.pk}),
        data={
            "barrier_plans": [barrier_plan.pk],
            "mount_plans": [],
            "road_marking_plans": [],
            "singpost_plans": [],
            "traffic_light_plans": [],
            "traffic_sign_plans": [],
            "additional_sign_plans": [],
            "furniture_signpost_plans": [],
        },
    )

    plan.refresh_from_db()
    assert response.status_code == 403
    assert plan.barrier_plans.count() == 0

    change_perm = Permission.objects.get(codename="change_plan", content_type=ct)
    user.user_permissions.add(change_perm)
    response = client.post(
        reverse("admin:traffic_control_plan_set-plans", kwargs={"object_id": plan.pk}),
        data={
            "barrier_plans": [barrier_plan.pk],
            "mount_plans": [],
            "road_marking_plans": [],
            "singpost_plans": [],
            "traffic_light_plans": [],
            "traffic_sign_plans": [],
            "additional_sign_plans": [],
            "furniture_signpost_plan": [],
        },
    )

    plan.refresh_from_db()
    assert response.status_code == 200
    assert plan.barrier_plans.count() == 1


@pytest.mark.parametrize("redirect_after_save", (False, True))
@pytest.mark.django_db
def test_plan_relation_admin_view_form_submit(admin_client, redirect_after_save):
    plan = get_plan()
    barrier_plan = get_barrier_plan()
    mount_plan = get_mount_plan()
    road_marking_plan = get_road_marking_plan()
    signpost_plan = get_signpost_plan()
    traffic_light_plan = get_traffic_light_plan()
    traffic_sign_plan = get_traffic_sign_plan()
    additional_sign_plan = AdditionalSignPlanFactory()
    furniture_signpost_plan = get_furniture_signpost_plan()

    for p in [
        signpost_plan,
        traffic_light_plan,
        traffic_sign_plan,
        additional_sign_plan,
        furniture_signpost_plan,
    ]:
        p.plan = plan
        p.save(update_fields=["plan"])

    url = reverse("admin:traffic_control_plan_set-plans", kwargs={"object_id": plan.pk})
    post_data = {
        "barrier_plans": [barrier_plan.pk],
        "mount_plans": [mount_plan.pk],
        "road_marking_plans": [road_marking_plan.pk],
        "singpost_plans": [],
        "traffic_light_plans": [],
        "traffic_sign_plans": [],
        "additional_sign_plans": [],
        "furniture_signpost_plan": [],
    }

    if redirect_after_save:
        # "Save" button press
        post_data["_save"] = "Save"
        response = admin_client.post(url, data=post_data)
        assert response.status_code == 302
    else:
        # "Save and continue editing" button press
        response = admin_client.post(url, data=post_data)
        assert response.status_code == 200

    plan.refresh_from_db()
    assert plan.barrier_plans.count() == 1
    assert plan.mount_plans.count() == 1
    assert plan.road_marking_plans.count() == 1
    assert plan.signpost_plans.count() == 0
    assert plan.traffic_light_plans.count() == 0
    assert plan.traffic_sign_plans.count() == 0
    assert plan.additional_sign_plans.count() == 0
    assert plan.furniture_signpost_plans.count() == 0


@pytest.mark.django_db
def test_plan_relation_admin_view_available_choices(admin_client):
    """
    Planned devices that are linked to other plan should not be listed as available choice.
    """
    plan_1 = get_plan(location=MultiPolygon(test_polygon, srid=settings.SRID))
    plan_2 = get_plan(location=MultiPolygon(test_polygon_2, srid=settings.SRID))

    for plan, loc, loc_3d in [
        (plan_1, test_point, test_point_3d),
        (plan_2, test_point_2, test_point_2_3d),
    ]:
        get_barrier_plan(location=loc, plan=plan)
        get_mount_plan(location=loc, plan=plan)
        get_road_marking_plan(location=loc, plan=plan)
        get_signpost_plan(location=loc, plan=plan)
        get_traffic_light_plan(location=loc, plan=plan)
        get_traffic_sign_plan(location=loc_3d, plan=plan)
        AdditionalSignPlanFactory(location=loc_3d, plan=plan)
        get_furniture_signpost_plan(location=loc, plan=plan)

    plan_1.refresh_from_db()
    plan_2.refresh_from_db()

    response = admin_client.get(reverse("admin:traffic_control_plan_set-plans", kwargs={"object_id": plan_1.pk}))

    form = response.context["form"]
    assert response.status_code == 200
    assert plan_2.barrier_plans.first() not in form.fields["barrier_plans"].queryset
    assert plan_2.mount_plans.first() not in form.fields["mount_plans"].queryset
    assert plan_2.road_marking_plans.first() not in form.fields["road_marking_plans"].queryset
    assert plan_2.signpost_plans.first() not in form.fields["signpost_plans"].queryset
    assert plan_2.traffic_light_plans.first() not in form.fields["traffic_light_plans"].queryset
    assert plan_2.traffic_sign_plans.first() not in form.fields["traffic_sign_plans"].queryset
    assert plan_2.additional_sign_plans.first() not in form.fields["additional_sign_plans"].queryset
    assert plan_2.furniture_signpost_plans.first() not in form.fields["furniture_signpost_plans"].queryset


@pytest.mark.parametrize(
    "factory",
    (
        AdditionalSignPlanFactory,
        get_barrier_plan,
        get_furniture_signpost_plan,
        get_mount_plan,
        get_road_marking_plan,
        get_signpost_plan,
        get_traffic_light_plan,
        get_traffic_sign_plan,
    ),
)
@pytest.mark.parametrize("derive_location", (False, True), ids=("no_derive_location", "derive_location"))
@pytest.mark.django_db
def test_plan_device_bulk_delete_update_plan_location(admin_client, factory, derive_location: bool):
    """
    Bulk-deleting planned devices using Admin UI should or should not update the Plan location
    depending on Plan's derive_location.
    """
    plan = get_plan(location=None, derive_location=derive_location)
    device1 = factory(location=test_point, plan=plan)
    device2 = factory(location=test_point_2, plan=plan)
    assert device1.id != device2.id

    plan.refresh_from_db()
    if derive_location:
        assert plan.location is not None
    else:
        assert plan.location is None

    plan_location_before_delete = plan.location
    response = admin_client.post(
        reverse(f"admin:{device1._meta.app_label}_{device1._meta.model_name}_changelist"),
        data={
            "action": "delete_selected",
            "_selected_action": [device1.id, device2.id],
            "post": "yes",
        },
    )
    assert response.status_code == 302

    plan.refresh_from_db()
    if derive_location:
        assert plan.location != plan_location_before_delete
    else:
        assert plan.location is None


@pytest.mark.django_db
def test__plan_create_illegal_location(admin_client):
    data = {"location": illegal_multipolygon.ewkt}
    response = admin_client.post(reverse("admin:traffic_control_plan_add"), data=data)
    assert response.status_code == 200
    assert Plan.objects.count() == 0
    assert "location" in response.context["adminform"].form.errors
    assert response.context["adminform"].form.errors["location"] == [f"Invalid location: {illegal_multipolygon.ewkt}"]


@pytest.mark.django_db
def test__plan_create_invalid_location_ewkt(admin_client):
    data = {"location_ewkt": invalid_ewkt_str}
    response = admin_client.post(reverse("admin:traffic_control_plan_add"), data=data)
    assert response.status_code == 200
    assert Plan.objects.count() == 0
    assert "location_ewkt" in response.context["adminform"].form.errors
    assert response.context["adminform"].form.errors["location_ewkt"] == ["Invalid location_ewkt value"]


@pytest.mark.django_db
def test__plan_update_location_using_location_field():
    """Test that updating location using location field, value from map widget, is not allowed"""
    orig_location = MultiPolygon(test_polygon, srid=settings.SRID)
    new_location = MultiPolygon(test_polygon, test_polygon_2, srid=settings.SRID)
    plan = PlanFactory(location=orig_location)
    data = {"location": new_location, "name": plan.name, "decision_id": plan.decision_id, "z_coord": 5}
    form = PlanModelForm(data, instance=plan)
    assert form.is_valid() is False
    assert form.errors["location"][0] == "Changing location from map is not allowed for geometry 'MultiPolygon'"
    plan.refresh_from_db()
    assert plan.location == orig_location


@pytest.mark.parametrize("derive_location", (False, True))
@pytest.mark.django_db
def test__plan_update_location_using_location_ewkt_field(derive_location):
    """Test that updating location using location_ewkt field can be done"""
    orig_location = MultiPolygon(test_polygon, srid=settings.SRID)
    new_location = MultiPolygon(test_polygon, test_polygon_2, srid=settings.SRID)
    plan = PlanFactory(location=orig_location)
    data = {
        "derive_location": derive_location,
        "location": orig_location,
        "location_ewkt": new_location.ewkt,
        "name": plan.name,
        "decision_id": plan.decision_id,
        "z_coord": 0,
    }
    form = PlanModelForm(data, instance=plan)
    assert form.is_valid() is True
    form.save()
    plan.refresh_from_db()
    assert plan.location.ewkt == new_location.ewkt


@pytest.mark.django_db
def test__plan_update_location_using_invalid_location_ewkt_field():
    orig_location = MultiPolygon(test_polygon, srid=settings.SRID)
    plan = PlanFactory(location=orig_location)
    data = {
        "location": orig_location,
        "location_ewkt": invalid_ewkt_str,
        "name": plan.name,
        "decision_id": plan.decision_id,
        "z_coord": 0,
    }
    form = PlanModelForm(data, instance=plan)
    assert form.is_valid() is False
    assert form.errors["location_ewkt"][0] == "Invalid location_ewkt value"


@pytest.mark.django_db
def test__plan_update_with_location_not_changed():
    """This is to test that not update location does not appered in auditlog"""
    location = MultiPolygon(test_polygon, srid=settings.SRID)
    plan = PlanFactory(location=location)
    logentries = LogEntry.objects.get_for_object(plan).filter(action=LogEntry.Action.CREATE)
    assert logentries.count() == 1
    assert Plan.objects.count() == 1

    data = {
        "location": location,
        "location_ewkt": location.ewkt,
        "name": plan.name,
        "decision_id": plan.decision_id,
        "z_coord": get_z_for_polygon(test_polygon),
    }
    form = PlanModelForm(data=data, instance=plan)
    assert form.is_valid() is True
    form.save()
    update_entries = LogEntry.objects.get_for_object(plan).filter(action=LogEntry.Action.UPDATE)
    assert update_entries.count() == 1
    update_entry = update_entries[0]
    assert "location_ewkt" not in update_entry.changes
    assert "location" not in update_entry.changes


@pytest.mark.django_db
def test__plan_update_to_empty_location():
    location = MultiPolygon(test_polygon, srid=settings.SRID)
    plan = PlanFactory(location=location)
    logentries = LogEntry.objects.get_for_object(plan).filter(action=LogEntry.Action.CREATE)
    assert logentries.count() == 1
    assert Plan.objects.count() == 1

    data = {
        "location": location,
        "location_ewkt": "",
        "name": plan.name,
        "decision_id": plan.decision_id,
        "z_coord": get_z_for_polygon(test_polygon),
    }
    form = PlanModelForm(data=data, instance=plan)
    assert form.is_valid() is True
    form.save()

    plan.refresh_from_db()
    assert plan.location is None


@pytest.mark.django_db
def test__plan_create_no_location():
    form = PlanModelForm(data=_get_plan_mandatory_fields())
    assert form.is_valid() is True
    form.save()
    assert Plan.objects.all().count() == 1


@pytest.mark.django_db
def test__plan_create_with_location_ewkt():
    data = _get_plan_mandatory_fields()
    data.update({"location_ewkt": test_multi_polygon.ewkt})
    form = PlanModelForm(data=data)

    assert form.is_valid() is True
    form.save()
    assert Plan.objects.all().count() == 1

    plan = Plan.objects.get()
    assert plan.location.ewkt == test_multi_polygon.ewkt


def _get_plan_mandatory_fields():
    return {"name": "testplan", "decision_id": "testid", "z_coord": 0}
