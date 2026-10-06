import re

import pytest
from auditlog.models import LogEntry
from django.contrib.admin import AdminSite
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status

from traffic_control.admin.admin_filters import DeviceTypeTagFilter
from traffic_control.admin.traffic_sign import (
    TrafficControlDeviceTypeAdmin,
    TrafficControlDeviceTypeTagAdmin,
)
from traffic_control.admin.views import DeviceTypeAutocompleteJsonView
from traffic_control.filters import TrafficControlDeviceTypeFilterSet
from traffic_control.forms import TrafficControlDeviceTypeTagForm
from traffic_control.models import TrafficControlDeviceType, TrafficControlDeviceTypeTag
from traffic_control.resources.device_type import TrafficControlDeviceTypeResource
from traffic_control.tests.factories import (
    get_api_client,
    get_user,
    TrafficControlDeviceTypeFactory,
    TrafficControlDeviceTypeTagFactory,
    UserFactory,
)
from traffic_control.tests.test_import_export.utils import file_formats, get_import_dataset


@pytest.fixture
def device_type_admin() -> TrafficControlDeviceTypeAdmin:
    return TrafficControlDeviceTypeAdmin(TrafficControlDeviceType, AdminSite())


@pytest.fixture
def tag_admin() -> TrafficControlDeviceTypeTagAdmin:
    return TrafficControlDeviceTypeTagAdmin(TrafficControlDeviceTypeTag, AdminSite())


@pytest.mark.django_db
def test__device_type_tag__str():
    """Tag is represented by its name."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")

    assert str(tag) == "Temporary"


@pytest.mark.django_db
def test__device_type_tag__many_to_many_relation():
    """Device types and tags have a many-to-many relation in both directions."""
    tag_1 = TrafficControlDeviceTypeTagFactory(name="Temporary")
    tag_2 = TrafficControlDeviceTypeTagFactory(name="Winter")
    device_type_1 = TrafficControlDeviceTypeFactory(code="DT-1", tags=[tag_1, tag_2])
    device_type_2 = TrafficControlDeviceTypeFactory(code="DT-2", tags=[tag_1])

    assert set(device_type_1.tags.all()) == {tag_1, tag_2}
    assert set(device_type_2.tags.all()) == {tag_1}
    assert set(tag_1.device_types.all()) == {device_type_1, device_type_2}
    assert set(tag_2.device_types.all()) == {device_type_1}


@pytest.mark.django_db
def test__device_type_tag__name_is_unique():
    """Two tags cannot share the same name."""
    TrafficControlDeviceTypeTagFactory(name="Temporary")
    duplicate = TrafficControlDeviceTypeTag(name="Temporary")

    with pytest.raises(ValidationError):
        duplicate.full_clean()


@pytest.mark.django_db
def test__device_type_tag_admin__lists_tags(rf, tag_admin):
    """Tag admin changelist shows created tags."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")
    request = rf.get("/")
    request.user = get_user(admin=True)

    changelist = tag_admin.get_changelist_instance(request)

    assert list(changelist.get_queryset(request)) == [tag]


@pytest.mark.django_db
def test__device_type_tag_admin__id_is_first_column(rf, tag_admin):
    """Tag admin changelist shows the id as its leading column."""
    TrafficControlDeviceTypeTagFactory(name="Temporary")
    request = rf.get("/")
    request.user = get_user(admin=True)

    changelist = tag_admin.get_changelist_instance(request)
    # Django prepends the bulk action checkbox, the first real column follows it.
    columns = [column for column in changelist.list_display if column != "action_checkbox"]

    assert columns == ["id", "name", "description", "device_type_count"]


@pytest.mark.django_db
def test__device_type_tag_admin__changelist_renders_id(admin_client):
    """Tag id is rendered on the tag admin changelist page."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")

    response = admin_client.get(reverse("admin:traffic_control_trafficcontroldevicetypetag_changelist"))

    assert response.status_code == status.HTTP_200_OK
    assert str(tag.id) in response.content.decode()


@pytest.mark.django_db
def test__device_type_tag_admin__change_view_contains_device_types_field(admin_client):
    """Device types can be selected from the tag change page."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")
    device_type = TrafficControlDeviceTypeFactory(code="DT-1", tags=[tag])

    response = admin_client.get(reverse("admin:traffic_control_trafficcontroldevicetypetag_change", args=(tag.pk,)))
    field = response.context["adminform"].form.fields["device_types"]

    assert response.status_code == status.HTTP_200_OK
    assert list(field.initial) == [device_type]


@pytest.mark.django_db
def test__device_type_tag_admin__change_view_saves_device_types(admin_client):
    """Saving the tag change form attaches and detaches device types."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")
    other_tag = TrafficControlDeviceTypeTagFactory(name="Winter")
    detached = TrafficControlDeviceTypeFactory(code="DT-1", tags=[tag, other_tag])
    attached = TrafficControlDeviceTypeFactory(code="DT-2")

    response = admin_client.post(
        reverse("admin:traffic_control_trafficcontroldevicetypetag_change", args=(tag.pk,)),
        data={"name": "Temporary", "description": "", "device_types": [str(attached.pk)]},
    )

    assert response.status_code == status.HTTP_302_FOUND
    assert list(tag.device_types.all()) == [attached]
    assert list(detached.tags.all()) == [other_tag], "Other tags of a detached device type must be kept"


@pytest.mark.django_db
def test__device_type_tag_admin__add_view_saves_device_types(admin_client):
    """A new tag can be created with device types already selected."""
    device_type = TrafficControlDeviceTypeFactory(code="DT-1")

    response = admin_client.post(
        reverse("admin:traffic_control_trafficcontroldevicetypetag_add"),
        data={"name": "Temporary", "description": "", "device_types": [str(device_type.pk)]},
    )
    created = TrafficControlDeviceTypeTag.objects.get(name="Temporary")

    assert response.status_code == status.HTTP_302_FOUND
    assert list(created.device_types.all()) == [device_type]


@pytest.mark.django_db
def test__device_type_tag_admin__saving_device_types_is_audit_logged(admin_client):
    """Attaching a device type from the tag page is logged in the device type's history."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")
    device_type = TrafficControlDeviceTypeFactory(code="DT-1")

    admin_client.post(
        reverse("admin:traffic_control_trafficcontroldevicetypetag_change", args=(tag.pk,)),
        data={"name": "Temporary", "description": "", "device_types": [str(device_type.pk)]},
    )
    log_entries = LogEntry.objects.get_for_object(device_type).filter(changes__has_key="tags")

    assert log_entries.count() == 1
    assert log_entries.first().changes["tags"]["objects"] == [str(tag)]


@pytest.mark.django_db
def test__device_type_tag_admin__device_type_autocomplete(admin_client):
    """The device type autocomplete endpoint returns device types matching the search term."""
    expected = TrafficControlDeviceTypeFactory(code="DT-MATCH")
    TrafficControlDeviceTypeFactory(code="DT-OTHER")

    response = admin_client.get(
        reverse("admin:traffic_control_trafficcontroldevicetypetag_devicetype_autocomplete"),
        {"term": "DT-MATCH"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "results": [{"id": str(expected.pk), "text": str(expected)}],
        "pagination": {"more": False},
    }


@pytest.mark.django_db
def test__device_type_tag_admin__device_type_autocomplete_is_paginated(admin_client):
    """The autocomplete endpoint pages the results and tells select2 that more results exist."""
    page_size = DeviceTypeAutocompleteJsonView.paginate_by
    for index in range(page_size + 1):
        TrafficControlDeviceTypeFactory(code=f"DT-{index:02d}")
    url = reverse("admin:traffic_control_trafficcontroldevicetypetag_devicetype_autocomplete")

    first_page = admin_client.get(url, {"term": "DT-"})
    second_page = admin_client.get(url, {"term": "DT-", "page": 2})

    assert len(first_page.json()["results"]) == page_size
    assert first_page.json()["pagination"]["more"] is True
    assert len(second_page.json()["results"]) == 1
    assert second_page.json()["pagination"]["more"] is False


@pytest.mark.django_db
def test__device_type_tag_admin__device_type_autocomplete_requires_view_permission(client):
    """A staff user without device type view permission is not allowed to search device types."""
    TrafficControlDeviceTypeFactory(code="DT-MATCH")
    client.force_login(UserFactory(is_staff=True))

    response = client.get(
        reverse("admin:traffic_control_trafficcontroldevicetypetag_devicetype_autocomplete"),
        {"term": "DT-MATCH"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test__device_type_tag_form__autocomplete_widget_renders_only_selected_device_types():
    """The device type widget renders the selected device types only and points to the endpoint."""
    selected = TrafficControlDeviceTypeFactory(code="DT-SELECTED")
    TrafficControlDeviceTypeFactory(code="DT-NOT-SELECTED")
    form = TrafficControlDeviceTypeTagForm(initial={"device_types": [selected.pk]})

    rendered = str(form["device_types"])

    assert reverse("admin:traffic_control_trafficcontroldevicetypetag_devicetype_autocomplete") in rendered
    assert "admin-autocomplete" in rendered
    assert rendered.count("<option") == 1
    assert str(selected) in rendered


@pytest.mark.django_db
def test__device_type_tag_admin__device_type_count_column(rf, tag_admin):
    """Tag changelist shows how many device types carry the tag."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")
    TrafficControlDeviceTypeFactory(code="DT-1", tags=[tag])
    TrafficControlDeviceTypeFactory(code="DT-2", tags=[tag])
    request = rf.get("/")
    request.user = get_user(admin=True)

    annotated = tag_admin.get_changelist_instance(request).get_queryset(request).get(pk=tag.pk)

    assert tag_admin.device_type_count(annotated) == 2


@pytest.mark.django_db
def test__device_type_admin__tag_list_column(device_type_admin):
    """Device type changelist renders the tag names of a device type."""
    device_type = TrafficControlDeviceTypeFactory(
        code="DT-1",
        tags=[
            TrafficControlDeviceTypeTagFactory(name="Alpha"),
            TrafficControlDeviceTypeTagFactory(name="Beta"),
        ],
    )

    assert device_type_admin.tag_list(device_type) == "Alpha, Beta"


@pytest.mark.django_db
def test__device_type_admin__search_by_tag_name(rf, device_type_admin):
    """Device type changelist can be searched with a tag name."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")
    expected = TrafficControlDeviceTypeFactory(code="DT-1", tags=[tag])
    TrafficControlDeviceTypeFactory(code="DT-2")

    request = rf.get("/", {"q": "Temporary"})
    request.user = get_user(admin=True)
    changelist = device_type_admin.get_changelist_instance(request)

    assert list(changelist.get_queryset(request)) == [expected]


@pytest.mark.django_db
def test__device_type_admin__change_view_contains_tags_field(admin_client):
    """Tags can be assigned from the device type change page."""
    device_type = TrafficControlDeviceTypeFactory(code="DT-1")
    TrafficControlDeviceTypeTagFactory(name="Temporary")

    response = admin_client.get(
        reverse("admin:traffic_control_trafficcontroldevicetype_change", args=(device_type.pk,))
    )

    assert response.status_code == status.HTTP_200_OK
    assert "tags" in response.context["adminform"].form.fields


@pytest.mark.django_db
def test__device_type_admin__filter_by_single_tag(rf, device_type_admin):
    """Changelist shows only device types carrying the selected tag."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")
    expected = TrafficControlDeviceTypeFactory(code="DT-1", tags=[tag])
    TrafficControlDeviceTypeFactory(code="DT-2")

    request = rf.get("/", {"tags": [str(tag.pk)]})
    request.user = get_user(admin=True)
    changelist = device_type_admin.get_changelist_instance(request)

    assert list(changelist.get_queryset(request)) == [expected]


@pytest.mark.django_db
def test__device_type_admin__filter_by_multiple_tags_any():
    """Default match mode returns device types having any of the selected tags."""
    admin_instance = TrafficControlDeviceTypeAdmin(TrafficControlDeviceType, AdminSite())
    temporary = TrafficControlDeviceTypeTagFactory(name="Temporary")
    winter = TrafficControlDeviceTypeTagFactory(name="Winter")
    only_temporary = TrafficControlDeviceTypeFactory(code="DT-1", tags=[temporary])
    only_winter = TrafficControlDeviceTypeFactory(code="DT-2", tags=[winter])
    both = TrafficControlDeviceTypeFactory(code="DT-3", tags=[temporary, winter])
    TrafficControlDeviceTypeFactory(code="DT-4")

    request = RequestFactory().get("/", {"tags": [str(temporary.pk), str(winter.pk)]})
    request.user = get_user(admin=True)
    changelist = admin_instance.get_changelist_instance(request)
    results = list(changelist.get_queryset(request))

    assert set(results) == {only_temporary, only_winter, both}
    assert len(results) == 3, "A device type matching several tags must not be duplicated"


@pytest.mark.django_db
def test__device_type_admin__filter_by_multiple_tags_all():
    """Match mode 'all' returns only device types carrying every selected tag."""
    admin_instance = TrafficControlDeviceTypeAdmin(TrafficControlDeviceType, AdminSite())
    temporary = TrafficControlDeviceTypeTagFactory(name="Temporary")
    winter = TrafficControlDeviceTypeTagFactory(name="Winter")
    TrafficControlDeviceTypeFactory(code="DT-1", tags=[temporary])
    TrafficControlDeviceTypeFactory(code="DT-2", tags=[winter])
    both = TrafficControlDeviceTypeFactory(code="DT-3", tags=[temporary, winter])

    request = RequestFactory().get(
        "/",
        {"tags": [str(temporary.pk), str(winter.pk)], "tags_match": "all"},
    )
    request.user = get_user(admin=True)
    changelist = admin_instance.get_changelist_instance(request)

    assert list(changelist.get_queryset(request)) == [both]


@pytest.mark.django_db
def test__device_type_admin__tag_filter_lookups_only_used_tags(rf, device_type_admin):
    """Filter offers only tags that are assigned to at least one device type."""
    used = TrafficControlDeviceTypeTagFactory(name="Used")
    TrafficControlDeviceTypeTagFactory(name="Unused")
    TrafficControlDeviceTypeFactory(code="DT-1", tags=[used])

    request = rf.get("/")
    request.user = get_user(admin=True)
    changelist = device_type_admin.get_changelist_instance(request)
    tag_filter = next(f for f in changelist.get_filters(request)[0] if isinstance(f, DeviceTypeTagFilter))

    assert tag_filter.lookup_choices == [(str(used.pk), "Used")]


@pytest.mark.django_db
def test__device_type_admin__tag_filter_renders_checkboxes(admin_client):
    """Tag filter renders a checkbox for each selectable tag on the changelist page."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")
    TrafficControlDeviceTypeFactory(code="DT-1", tags=[tag])

    response = admin_client.get(reverse("admin:traffic_control_trafficcontroldevicetype_changelist"))
    content = response.content.decode()

    assert response.status_code == status.HTTP_200_OK
    assert "multiselect-tag-filter" in content
    assert re.search(rf"<input[^>]*multiselect-tag-filter-value[^>]*value=\"{tag.pk}\"[^>]*>", content) is not None
    assert 'type="checkbox"' in content


@pytest.mark.django_db
def test__device_type_admin__tag_filter_checkbox_is_checked_when_selected(admin_client):
    """Checkbox of an active tag is pre-checked when returning to the filtered changelist."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")
    TrafficControlDeviceTypeFactory(code="DT-1", tags=[tag])

    url = reverse("admin:traffic_control_trafficcontroldevicetype_changelist")
    response = admin_client.get(url, {"tags": str(tag.pk)})
    content = response.content.decode()
    checkbox = re.search(rf"<input[^>]*multiselect-tag-filter-value[^>]*value=\"{tag.pk}\"[^>]*>", content)

    assert response.status_code == status.HTTP_200_OK
    assert checkbox is not None
    assert "checked" in checkbox.group(0)


@pytest.mark.django_db
def test__device_type_api__tags_are_serialized():
    """Device type API response contains the related tags."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary", description="Temporary devices")
    device_type = TrafficControlDeviceTypeFactory(code="DT-1", tags=[tag])
    api_client = get_api_client(user=get_user())

    response = api_client.get(reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.pk}))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["tags"] == [
        {"id": str(tag.id), "name": "Temporary", "description": "Temporary devices"},
    ]


@pytest.mark.django_db
def test__device_type_api__tags_can_be_assigned():
    """Admin can assign tags to a device type through the API."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")
    device_type = TrafficControlDeviceTypeFactory(code="DT-1")
    api_client = get_api_client(user=get_user(admin=True))

    response = api_client.patch(
        reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.pk}),
        data={"tag_ids": [str(tag.id)]},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert list(device_type.tags.all()) == [tag]


@pytest.mark.django_db
@pytest.mark.parametrize("filter_field", ("tags", "tag_name"))
def test__device_type_api__filter_by_tag(filter_field):
    """Device type list can be filtered by tag id and by tag name."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")
    expected = TrafficControlDeviceTypeFactory(code="DT-1", tags=[tag])
    TrafficControlDeviceTypeFactory(code="DT-2")
    api_client = get_api_client(user=get_user())
    filter_value = str(tag.id) if filter_field == "tags" else tag.name

    response = api_client.get(reverse("v1:trafficcontroldevicetype-list"), {filter_field: filter_value})

    assert response.status_code == status.HTTP_200_OK
    assert [result["id"] for result in response.data["results"]] == [str(expected.id)]


@pytest.fixture
def tagged_device_types():
    """Create device types carrying overlapping tag combinations.

    Returns:
        tuple: The tags ``a`` and ``b`` used by the created device types.
    """
    tag_a = TrafficControlDeviceTypeTagFactory(name="Alpha")
    tag_b = TrafficControlDeviceTypeTagFactory(name="Beta")
    TrafficControlDeviceTypeFactory(code="DT-BOTH", tags=[tag_a, tag_b])
    TrafficControlDeviceTypeFactory(code="DT-ONLY-A", tags=[tag_a])
    TrafficControlDeviceTypeFactory(code="DT-NONE")
    return tag_a, tag_b


def _get_codes(response) -> list:
    """Collect device type codes from a list endpoint response.

    Args:
        response: The API response to read results from.

    Returns:
        list: Sorted device type codes contained in the response.
    """
    return sorted(result["code"] for result in response.data["results"])


@pytest.mark.django_db
def test__device_type_api__filter_by_multiple_tags_defaults_to_any(tagged_device_types):
    """Repeated tags parameters match device types having any of the given tags."""
    tag_a, tag_b = tagged_device_types
    api_client = get_api_client(user=get_user())
    url = reverse("v1:trafficcontroldevicetype-list")

    response = api_client.get(f"{url}?tags={tag_a.id}&tags={tag_b.id}")

    assert response.status_code == status.HTTP_200_OK
    assert _get_codes(response) == ["DT-BOTH", "DT-ONLY-A"]


@pytest.mark.django_db
@pytest.mark.parametrize("match_value", ("", "any"), ids=("empty", "explicit_any"))
def test__device_type_api__tags_match_is_optional(tagged_device_types, match_value):
    """Omitting or emptying the match mode keeps the default any behaviour."""
    tag_a, tag_b = tagged_device_types
    api_client = get_api_client(user=get_user())
    url = reverse("v1:trafficcontroldevicetype-list")

    response = api_client.get(f"{url}?tags={tag_a.id}&tags={tag_b.id}&tags_match={match_value}")

    assert response.status_code == status.HTTP_200_OK
    assert _get_codes(response) == ["DT-BOTH", "DT-ONLY-A"]


def test__device_type_filterset__tags_match_field_is_not_required():
    """The match mode form field is optional so plain tag filtering needs no extra parameter."""
    filterset = TrafficControlDeviceTypeFilterSet()

    assert filterset.filters["tags_match"].field.required is False


@pytest.mark.django_db
def test__device_type_api__filter_by_multiple_tags_all(tagged_device_types):
    """Match mode all requires the device type to carry every selected tag."""
    tag_a, tag_b = tagged_device_types
    api_client = get_api_client(user=get_user())
    url = reverse("v1:trafficcontroldevicetype-list")

    response = api_client.get(f"{url}?tags={tag_a.id}&tags={tag_b.id}&tags_match=all")

    assert response.status_code == status.HTTP_200_OK
    assert _get_codes(response) == ["DT-BOTH"]


@pytest.mark.django_db
def test__device_type_api__filter_by_multiple_tags_any_has_no_duplicates(tagged_device_types):
    """A device type matching several selected tags is returned only once."""
    tag_a, tag_b = tagged_device_types
    api_client = get_api_client(user=get_user())
    url = reverse("v1:trafficcontroldevicetype-list")

    response = api_client.get(f"{url}?tags={tag_a.id}&tags={tag_b.id}")
    codes = _get_codes(response)

    assert response.status_code == status.HTTP_200_OK
    assert codes.count("DT-BOTH") == 1
    assert response.data["count"] == len(codes)


@pytest.mark.django_db
def test__device_type_api__filter_by_tag_name_is_case_insensitive():
    """Tag name filtering ignores character casing."""
    tag = TrafficControlDeviceTypeTagFactory(name="Temporary")
    expected = TrafficControlDeviceTypeFactory(code="DT-1", tags=[tag])
    api_client = get_api_client(user=get_user())

    response = api_client.get(reverse("v1:trafficcontroldevicetype-list"), {"tag_name": "tEmPoRaRy"})

    assert response.status_code == status.HTTP_200_OK
    assert [result["id"] for result in response.data["results"]] == [str(expected.id)]


@pytest.mark.django_db
def test__device_type_api__filter_by_unused_tag_returns_empty_result():
    """Filtering by a tag without device types returns no results."""
    TrafficControlDeviceTypeFactory(code="DT-1", tags=[TrafficControlDeviceTypeTagFactory(name="Used")])
    unused = TrafficControlDeviceTypeTagFactory(name="Unused")
    api_client = get_api_client(user=get_user())

    response = api_client.get(reverse("v1:trafficcontroldevicetype-list"), {"tags": str(unused.id)})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"] == []


@pytest.mark.django_db
def test__device_type_api__invalid_tags_match_is_rejected(tagged_device_types):
    """An unsupported match mode results in a bad request instead of being ignored."""
    tag_a, _tag_b = tagged_device_types
    api_client = get_api_client(user=get_user())
    url = reverse("v1:trafficcontroldevicetype-list")

    response = api_client.get(f"{url}?tags={tag_a.id}&tags_match=sometimes")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test__device_type_resource__export_includes_tags():
    """Export contains a tags column with comma separated tag names."""
    TrafficControlDeviceTypeFactory(
        code="DT-1",
        tags=[
            TrafficControlDeviceTypeTagFactory(name="Beta"),
            TrafficControlDeviceTypeTagFactory(name="Alpha"),
        ],
    )

    dataset = TrafficControlDeviceTypeResource().export()
    exported = next(row for row in dataset.dict if row["code"] == "DT-1")

    assert exported["tags"] == "Alpha,Beta"


@pytest.mark.django_db
@pytest.mark.parametrize("format", file_formats)
def test__device_type_resource__import_links_and_creates_tags(format):
    """Import links existing tags and creates missing ones."""
    existing_tag = TrafficControlDeviceTypeTagFactory(name="Alpha")
    TrafficControlDeviceTypeFactory(code="DT-1", tags=[existing_tag])
    dataset = get_import_dataset(TrafficControlDeviceTypeResource, format=format)
    del dataset["tags"]
    dataset.append_col(["Alpha,Gamma"] * len(dataset), header="tags")

    result = TrafficControlDeviceTypeResource().import_data(dataset, raise_errors=False)

    assert not result.has_errors()
    assert not result.has_validation_errors()
    imported = TrafficControlDeviceType.objects.get(code="DT-1")
    assert sorted(imported.tags.values_list("name", flat=True)) == ["Alpha", "Gamma"]
    assert TrafficControlDeviceTypeTag.objects.filter(name="Gamma").exists()
