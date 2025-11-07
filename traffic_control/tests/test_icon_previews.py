import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains

from traffic_control.tests.factories import (
    TrafficControlDeviceTypeFactory,
    TrafficControlDeviceTypeIconFactory,
    TrafficSignPlanFactory,
)

# NOTE (2025-11-13 thiago)
# These are somewhat low-effort tests for the presence of an icon preview in detail / list views for many models. They
# simply detect the presence of a src="{icon.file.url}" substring in the response and deem it a good enough proof that
# an icon preview was generated, since it's so unlikely that anything other than an <img src="{icon.file.url}" /> would
# show up with that text. Should the need for a more precise test for these previews (for example good placement in a
# document flow, styles, etc) arise, these tests should be updated accordingly


@pytest.mark.django_db
def test__preview_image_file_field_mixin__list_view(admin_client):
    icon = TrafficControlDeviceTypeIconFactory()
    list_url = reverse("admin:traffic_control_trafficcontroldevicetypeicon_changelist")
    response = admin_client.get(list_url)
    assertContains(response, f'src="{icon.file.url}"')


@pytest.mark.django_db
def test__preview_image_file_field_mixin__detail_view(admin_client):
    icon = TrafficControlDeviceTypeIconFactory()
    detail_url = reverse("admin:traffic_control_trafficcontroldevicetypeicon_change", args=[icon.pk])
    response = admin_client.get(detail_url)
    assertContains(response, f'src="{icon.file.url}"')


@pytest.mark.django_db
def test__preview_icon_file_relation_mixin__list_view(admin_client):
    device_type = TrafficControlDeviceTypeFactory()
    list_url = reverse("admin:traffic_control_trafficcontroldevicetype_changelist")
    response = admin_client.get(list_url)
    assertContains(response, f'src="{device_type.icon_file.file.url}"')


@pytest.mark.django_db
def test__preview_icon_file_relation_mixin__detail_view(admin_client):
    device_type = TrafficControlDeviceTypeFactory()
    detail_url = reverse("admin:traffic_control_trafficcontroldevicetype_change", args=[device_type.pk])
    response = admin_client.get(detail_url)
    assertContains(response, f'src="{device_type.icon_file.file.url}"')


@pytest.mark.django_db
def test_preview_device_type_relation_mixin__list_view(admin_client):
    traffic_sign = TrafficSignPlanFactory()
    list_url = reverse("admin:traffic_control_trafficsignplan_changelist")
    response = admin_client.get(list_url)
    assertContains(response, f'src="{traffic_sign.device_type.icon_file.file.url}"')


@pytest.mark.django_db
def test_preview_device_type_relation_mixin__detail_view(admin_client):
    traffic_sign = TrafficSignPlanFactory()
    detail_url = reverse("admin:traffic_control_trafficsignplan_change", args=[traffic_sign.pk])
    response = admin_client.get(detail_url)
    # NOTE (2025-11-13 thiago)
    # This is a weaker test of image previews. Device type dropdown selectors render the images as a side effect of
    # rendering the dropdown, so we check that the device_type object is referenced in a dropdown's options. To test
    # this properly we'd need to run JavaScript, and I'm not feeling like checking this little detail is enough reason
    # to bring selenium, playwright or some other beefy full-browser test framework to the project, but maybe the test
    # warrants an update if some other feature brings it.
    assertContains(response, '<img class="traffic-sign-icon"')
    assertContains(response, f'<option value="{traffic_sign.device_type.pk}"')
