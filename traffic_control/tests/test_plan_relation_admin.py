import importlib

import django.urls.resolvers
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import MultiPolygon
from django.test import override_settings
from django.urls import reverse

from ..models import Plan
from .factories import (
    get_barrier_plan,
    get_mount_plan,
    get_plan,
    get_road_marking_plan,
    get_signpost_plan,
    get_traffic_light_plan,
    get_traffic_sign_plan,
    get_user,
)
from .test_base_api import test_point, test_point_2, test_polygon, test_polygon_2
from .test_base_api_3d import test_point_2_3d, test_point_3d

settings_overrides = override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
)


def setup_module():
    settings_overrides.enable()
    _reload_urls()


def teardown_module():
    settings_overrides.disable()
    _reload_urls()


def _reload_urls():
    urls = importlib.import_module("city-infrastructure-platform.urls")
    importlib.reload(urls)
    django.urls.resolvers.get_resolver.cache_clear()


@pytest.mark.django_db
def test_plan_relation_admin_view_requires_view_permission(client):
    user = get_user()
    get_user_model().objects.filter(pk=user.pk).update(is_staff=True)
    plan = get_plan()
    client.force_login(user)

    response = client.get(
        reverse("admin:traffic_control_plan_set-plans", kwargs={"object_id": plan.pk})
    )
    assert response.status_code == 403

    ct = ContentType.objects.get_for_model(Plan)
    view_perm = Permission.objects.get(codename="view_plan", content_type=ct)
    user.user_permissions.add(view_perm)
    response = client.get(
        reverse("admin:traffic_control_plan_set-plans", kwargs={"object_id": plan.pk})
    )
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

    for p in [signpost_plan, traffic_light_plan, traffic_sign_plan]:
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


@pytest.mark.django_db
def test_plan_relation_admin_view_available_choices(admin_client):
    """
    BarrierPlans, MountPlans, RoadMarkingPlans, SignpostPlans, TrafficLightPlans,
    and TrafficSignPlans that are linked to other plan should not be listed as
    available choice.
    """
    plan_1 = get_plan(location=MultiPolygon(test_polygon, srid=settings.SRID))
    plan_2 = get_plan(location=MultiPolygon(test_polygon_2, srid=settings.SRID))

    for plan, loc, loc_3d in [
        (plan_1, test_point, test_point_3d),
        (plan_2, test_point_2, test_point_2_3d),
    ]:
        bp = get_barrier_plan(location=loc)
        mp = get_mount_plan(location=loc)
        rmp = get_road_marking_plan(location=loc)
        sp = get_signpost_plan(location=loc)
        tlp = get_traffic_light_plan(location=loc)
        tsp = get_traffic_sign_plan(location=loc_3d)

        for p in [bp, mp, rmp, sp, tlp, tsp]:
            p.plan = plan
            p.save(update_fields=["plan"])

    plan_1.refresh_from_db()
    plan_2.refresh_from_db()

    response = admin_client.get(
        reverse("admin:traffic_control_plan_set-plans", kwargs={"object_id": plan_1.pk})
    )

    form = response.context["form"]
    assert response.status_code == 200
    assert plan_2.barrier_plans.first() not in form.fields["barrier_plans"].queryset
    assert plan_2.mount_plans.first() not in form.fields["mount_plans"].queryset
    assert (
        plan_2.road_marking_plans.first()
        not in form.fields["road_marking_plans"].queryset
    )
    assert plan_2.signpost_plans.first() not in form.fields["signpost_plans"].queryset
    assert (
        plan_2.traffic_light_plans.first()
        not in form.fields["traffic_light_plans"].queryset
    )
    assert (
        plan_2.traffic_sign_plans.first()
        not in form.fields["traffic_sign_plans"].queryset
    )
