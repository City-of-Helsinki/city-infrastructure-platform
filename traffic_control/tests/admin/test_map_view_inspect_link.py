import factory
import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse

from city_furniture.tests.factories import FurnitureSignpostRealFactory
from map.tests.factories import FeatureTypeEditMappingFactory, LayerFactory
from traffic_control.enums import Lifecycle
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    BarrierRealFactory,
    get_user,
    MountPlanFactory,
    MountRealFactory,
    ResponsibleEntityFactory,
    SignpostPlanFactory,
    SignpostRealFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)

LINK_TEXT = "Inspect feature in map view"
LINK_CSS = "traffic_control/css/map_view_inspect_link.css"


def _change_url(obj: object) -> str:
    """Returns the admin change view URL of the given object.

    Args:
        obj (object): A saved model instance.

    Returns:
        str: The admin change view URL.
    """
    return reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk])


@pytest.fixture(autouse=True)
def english(settings):
    settings.LANGUAGE_CODE = "en"
    return settings


@pytest.mark.parametrize(
    "device_factory",
    (
        TrafficSignRealFactory,
        TrafficSignPlanFactory,
        AdditionalSignRealFactory,
        SignpostRealFactory,
        SignpostPlanFactory,
    ),
)
@pytest.mark.django_db
def test_change_view_shows_inspect_link(admin_client: Client, device_factory: type[factory.Factory]) -> None:
    obj = device_factory()
    LayerFactory(identifier=obj._meta.model_name)

    response = admin_client.get(_change_url(obj))

    assert response.status_code == 200
    content = response.content.decode()
    assert LINK_TEXT in content
    assert f"inspect_layer={obj._meta.model_name}&amp;inspect_id={obj.pk}" in content
    assert LINK_CSS in content


@pytest.mark.parametrize("device_factory", (MountRealFactory, MountPlanFactory))
@pytest.mark.django_db
def test_mount_change_view_links_to_centroid_layer(admin_client: Client, device_factory: type[factory.Factory]) -> None:
    obj = device_factory()
    centroid_layer = f"{obj._meta.model_name}centroid"
    LayerFactory(identifier=centroid_layer)
    FeatureTypeEditMappingFactory(name=centroid_layer, edit_name=obj._meta.model_name)

    response = admin_client.get(_change_url(obj))

    assert f"inspect_layer={centroid_layer}&amp;inspect_id={obj.pk}" in response.content.decode()


@pytest.mark.django_db
def test_change_view_without_layer_has_no_inspect_link(admin_client: Client) -> None:
    response = admin_client.get(_change_url(TrafficSignRealFactory()))

    assert response.status_code == 200
    assert LINK_TEXT not in response.content.decode()


@pytest.mark.django_db
def test_soft_deleted_object_has_no_inspect_link(admin_client: Client) -> None:
    LayerFactory(identifier="trafficsignreal")
    traffic_sign = TrafficSignRealFactory()
    traffic_sign.soft_delete(get_user())

    response = admin_client.get(_change_url(traffic_sign))

    assert LINK_TEXT not in response.content.decode()


@pytest.mark.django_db
def test_add_view_has_no_inspect_link(admin_client: Client) -> None:
    LayerFactory(identifier="trafficsignreal")

    response = admin_client.get(reverse("admin:traffic_control_trafficsignreal_add"))

    assert response.status_code == 200
    assert LINK_TEXT not in response.content.decode()


@pytest.mark.django_db
def test_object_not_in_map_view_has_no_inspect_link(admin_client: Client) -> None:
    LayerFactory(identifier="trafficsignreal")
    traffic_sign = TrafficSignRealFactory(lifecycle=Lifecycle.INACTIVE)

    response = admin_client.get(_change_url(traffic_sign))

    assert response.status_code == 200
    assert LINK_TEXT not in response.content.decode()


@pytest.mark.django_db
def test_model_without_wfs_feature_type_has_no_inspect_link(admin_client: Client) -> None:
    barrier = BarrierRealFactory()
    LayerFactory(identifier=barrier._meta.model_name)

    response = admin_client.get(_change_url(barrier))

    assert response.status_code == 200
    assert LINK_TEXT not in response.content.decode()


@pytest.fixture
def view_only_client(client: Client) -> Client:
    """Returns a client logged in as a staff user who can only view traffic sign reals.

    Args:
        client (Client): The Django test client.

    Returns:
        Client: The logged in client.
    """
    user = get_user(bypass_responsible_entity=True)
    user.is_staff = True
    user.save()
    user.user_permissions.add(Permission.objects.get(codename="view_trafficsignreal"))
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_view_only_change_view_shows_read_only_map_with_inspect_link(view_only_client: Client) -> None:
    LayerFactory(identifier="trafficsignreal")
    traffic_sign = TrafficSignRealFactory()

    response = view_only_client.get(_change_url(traffic_sign))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'id="id_location_map"' in content
    assert "OLMapWidget.js" in content
    assert "disableDrawing()" in content
    assert "Delete all Features" not in content
    assert f"inspect_layer=trafficsignreal&amp;inspect_id={traffic_sign.pk}" in content
    assert LINK_CSS in content


@pytest.mark.django_db
def test_view_only_change_view_without_layer_shows_map_without_link(view_only_client: Client) -> None:
    response = view_only_client.get(_change_url(TrafficSignRealFactory()))

    content = response.content.decode()
    assert 'id="id_location_map"' in content
    assert LINK_TEXT not in content


@pytest.mark.django_db
def test_editable_change_view_map_is_not_read_only(admin_client: Client) -> None:
    response = admin_client.get(_change_url(TrafficSignRealFactory()))

    content = response.content.decode()
    assert "Delete all Features" in content
    assert "disableDrawing()" not in content


@pytest.mark.django_db
def test_object_of_other_responsible_entity_shows_read_only_map_with_inspect_link(client: Client) -> None:
    LayerFactory(identifier="furnituresignpostreal", app_name="city_furniture")
    signpost = FurnitureSignpostRealFactory(responsible_entity=ResponsibleEntityFactory(name="Other entity"))
    user = get_user()
    user.is_staff = True
    user.save()
    codenames = ["view_furnituresignpostreal", "change_furnituresignpostreal"]
    user.user_permissions.add(*Permission.objects.filter(codename__in=codenames))
    client.force_login(user)

    response = client.get(_change_url(signpost))

    assert response.status_code == 200
    content = response.content.decode()
    assert "disableDrawing()" in content
    assert f"inspect_layer=furnituresignpostreal&amp;inspect_id={signpost.pk}" in content
