from datetime import datetime

import pytest
from auditlog.models import LogEntry
from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.gis.geos import Point
from django.urls import resolve, reverse

from traffic_control.admin import BarrierRealAdmin, TrafficSignRealAdmin
from traffic_control.enums import Lifecycle
from traffic_control.models import BarrierReal, TrafficSignReal
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    BarrierRealFactory,
    get_owner,
    get_user,
    TrafficSignRealFactory,
)
from traffic_control.tests.utils import MIN_X, MIN_Y


class MockRequest:
    pass


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------


@pytest.fixture
def standard_user():
    return get_user()


@pytest.fixture
def admin_user():
    return get_user(admin=True)


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def traffic_sign_real(standard_user):
    return TrafficSignRealFactory(
        location=Point(MIN_X + 10, MIN_Y + 5, 5, srid=settings.SRID),
        legacy_code="100",
        direction=0,
        created_by=standard_user,
        updated_by=standard_user,
        owner=get_owner(),
        lifecycle=Lifecycle.ACTIVE,
    )


@pytest.fixture
def barrier_real():
    return BarrierRealFactory()


@pytest.fixture
def barrier_admin(admin_site):
    return BarrierRealAdmin(BarrierReal, admin_site)


# ------------------------------------------------------------------------------
# TrafficSignRealAdmin Tests
# ------------------------------------------------------------------------------


@pytest.mark.django_db
def test_traffic_sign_real_admin_display_map_widget_for_location(admin_user, traffic_sign_real, admin_site):
    ma = TrafficSignRealAdmin(TrafficSignReal, admin_site)
    request = MockRequest()
    request.user = admin_user
    form = ma.get_form(request, traffic_sign_real)
    assert type(form.base_fields["location"].widget).__name__ == "CityInfra3DOSMWidget"


@pytest.mark.django_db
def test_traffic_sign_admin_has_a_z_coord_field(admin_user, traffic_sign_real, admin_site):
    ma = TrafficSignRealAdmin(TrafficSignReal, admin_site)
    request = MockRequest()
    request.user = admin_user
    form = ma.get_form(request, traffic_sign_real)
    assert "z_coord" in form.base_fields


@pytest.mark.django_db
def test_has_additional_signs_return_yes(rf, traffic_sign_real, admin_site):
    AdditionalSignRealFactory(parent=traffic_sign_real)
    ma = TrafficSignRealAdmin(TrafficSignReal, admin_site)

    # NOTE: Since the admin class has_additional_signs method operates over annotated objects,
    # we need to make use of the queries produced by its admin page.
    list_url = reverse("admin:traffic_control_trafficsignreal_changelist")
    request = rf.get(list_url)
    request.resolver_match = resolve(list_url)

    qs = ma.get_queryset(request)
    obj_with_annotation = qs.get(pk=traffic_sign_real.pk)

    assert ma.has_additional_signs(obj_with_annotation) == "Yes"


@pytest.mark.django_db
def test_has_additional_signs_return_no(rf, traffic_sign_real, admin_site):
    ma = TrafficSignRealAdmin(TrafficSignReal, admin_site)

    list_url = reverse("admin:traffic_control_trafficsignreal_changelist")
    request = rf.get(list_url)
    qs = ma.get_queryset(request)
    obj_with_annotation = qs.get(pk=traffic_sign_real.pk)

    assert ma.has_additional_signs(obj_with_annotation) == "No"


@pytest.mark.django_db
def test_save_model_set_created_by_and_updated_by_for_creating(admin_user, admin_site):
    ma = TrafficSignRealAdmin(TrafficSignReal, admin_site)
    request = MockRequest()
    request.user = admin_user
    new_traffic_sign_real = TrafficSignRealFactory(
        location=Point(MIN_X + 1, MIN_Y + 1, 5, srid=settings.SRID),
        legacy_code="100",
        direction=0,
        owner=get_owner(),
        created_by=admin_user,
    )
    ma.save_model(request, new_traffic_sign_real, None, None)

    assert new_traffic_sign_real.updated_by == admin_user
    assert new_traffic_sign_real.created_by == admin_user


@pytest.mark.django_db
def test_save_model_set_updated_by_for_updating(admin_user, standard_user, traffic_sign_real, admin_site):
    ma = TrafficSignRealAdmin(TrafficSignReal, admin_site)
    request = MockRequest()
    request.user = admin_user
    ma.save_model(request, traffic_sign_real, None, None)

    assert traffic_sign_real.created_by == standard_user
    assert traffic_sign_real.updated_by == admin_user


# ------------------------------------------------------------------------------
# SoftDeleteAdmin Tests
# ------------------------------------------------------------------------------


@pytest.mark.django_db
def test_exclude_soft_deleted_by_default(rf, admin_user, barrier_admin, barrier_real):
    request = rf.get("/")
    request.user = admin_user
    changelist = barrier_admin.get_changelist_instance(request)

    qs = changelist.get_queryset(request)
    assert qs.count() == 1

    barrier_admin.delete_model(request, barrier_real)
    qs = barrier_admin.get_queryset(request)
    assert qs.count() == 0


@pytest.mark.django_db
def test_list_soft_deleted(rf, admin_user, barrier_admin, barrier_real):
    request = rf.get("/", {"soft_deleted": "1"})
    request.user = admin_user
    changelist = barrier_admin.get_changelist_instance(request)

    qs = changelist.get_queryset(request)
    assert qs.count() == 0

    barrier_real.soft_delete(admin_user)
    qs = changelist.get_queryset(request)
    assert qs.count() == 1


@pytest.mark.django_db
def test_action_soft_delete(rf, admin_user, barrier_admin, barrier_real):
    request = rf.post("/")
    request.user = admin_user
    barrier_admin.action_soft_delete(request, BarrierReal.objects.all())
    barrier_real.refresh_from_db()

    assert not barrier_real.is_active
    assert isinstance(barrier_real.deleted_at, datetime)
    assert barrier_real.deleted_by == admin_user

    # LogEntries appear to be done by system user as no login is actually performed -> actor == None.
    create_entries = LogEntry.objects.get_for_object(barrier_real).filter(action=LogEntry.Action.CREATE)
    assert create_entries.count() == 1
    create_entry = create_entries[0]
    assert create_entry.actor is None

    update_entries = LogEntry.objects.get_for_object(barrier_real).filter(action=LogEntry.Action.UPDATE)
    assert update_entries.count() == 1
    update_entry = update_entries[0]
    assert update_entry.actor is None


# ------------------------------------------------------------------------------
# AdditionalSignPlan Filter Tests
# ------------------------------------------------------------------------------


@pytest.mark.django_db
def test_additional_sign_plan_lifecycle_filter_highlights_selected_option(admin_client):
    # Adjust the URL if your app_name/model_name differs slightly
    url = reverse("admin:traffic_control_additionalsignplan_changelist")
    selected_value = Lifecycle.ACTIVE.value

    # 1. Perform the GET request with the filter applied
    response = admin_client.get(url, {"lifecycle__exact": selected_value})
    assert response.status_code == 200

    # 2. Extract the ChangeList object from the template context
    cl = response.context["cl"]

    # 3. Find the filter instance specifically for the 'lifecycle' field
    lifecycle_filter = next(f for f in cl.filter_specs if getattr(f, "field_path", "") == "lifecycle")

    # 4. Extract the choices dictionaries generated by this filter
    choices = list(lifecycle_filter.choices(cl))

    # 5. Find the dictionary for our selected choice
    target_choice = next(c for c in choices if f"lifecycle__exact={selected_value}" in c.get("query_string", ""))

    # 6. Assert that Django's internal logic flagged this choice as selected
    assert target_choice["selected"] is True

    # Ensure the "All" choice is NOT selected
    all_choice = choices[0]
    assert all_choice["selected"] is False
