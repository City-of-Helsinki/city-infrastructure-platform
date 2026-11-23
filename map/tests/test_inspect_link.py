from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest
from django.urls import reverse

from map.services.inspect_link import (
    build_map_view_inspect_url,
    get_inspect_layer_identifier,
    get_map_view_base_url,
)
from map.tests.factories import FeatureTypeEditMappingFactory, LayerFactory
from traffic_control.enums import Lifecycle
from traffic_control.models import MountReal, TrafficSignReal
from traffic_control.tests.factories import (
    BarrierRealFactory,
    get_traffic_sign_plan,
    get_user,
    MountRealFactory,
    TrafficSignRealFactory,
)


def test_map_view_base_url_defaults_to_django_map_view(settings) -> None:
    settings.MAP_VIEW_URL = ""
    assert get_map_view_base_url() == reverse("map-view")


def test_map_view_base_url_uses_setting(settings) -> None:
    settings.MAP_VIEW_URL = "http://localhost:5173/"
    assert get_map_view_base_url() == "http://localhost:5173/"


@pytest.mark.django_db
def test_layer_identifier_matches_model_name() -> None:
    LayerFactory(identifier="trafficsignreal")
    assert get_inspect_layer_identifier(TrafficSignReal) == "trafficsignreal"


@pytest.mark.django_db
def test_layer_identifier_found_through_feature_type_edit_mapping() -> None:
    LayerFactory(identifier="mountrealcentroid")
    FeatureTypeEditMappingFactory(name="mountrealcentroid", edit_name="mountreal")
    assert get_inspect_layer_identifier(MountReal) == "mountrealcentroid"


@pytest.mark.django_db
def test_layer_identifier_prefers_model_name_over_mapping() -> None:
    LayerFactory(identifier="mountrealcentroid")
    LayerFactory(identifier="mountreal")
    FeatureTypeEditMappingFactory(name="mountrealcentroid", edit_name="mountreal")
    assert get_inspect_layer_identifier(MountReal) == "mountreal"


@pytest.mark.parametrize(
    "layer_kwargs",
    (
        pytest.param({"identifier": "trafficsignplan"}, id="other-model"),
        pytest.param({"identifier": "trafficsignreal", "app_name": "city_furniture"}, id="other-app"),
        pytest.param({"identifier": "trafficsignreal", "is_basemap": True}, id="basemap"),
    ),
)
@pytest.mark.django_db
def test_layer_identifier_none_when_no_matching_overlay(layer_kwargs: dict) -> None:
    LayerFactory(**layer_kwargs)
    assert get_inspect_layer_identifier(TrafficSignReal) is None


@pytest.mark.django_db
def test_inspect_url_contains_layer_and_id(settings) -> None:
    settings.MAP_VIEW_URL = ""
    LayerFactory(identifier="trafficsignreal")
    traffic_sign = TrafficSignRealFactory()

    url = urlparse(build_map_view_inspect_url(traffic_sign))

    assert url.path == reverse("map-view")
    assert parse_qs(url.query) == {"inspect_layer": ["trafficsignreal"], "inspect_id": [str(traffic_sign.pk)]}


@pytest.mark.django_db
def test_inspect_url_uses_map_view_url_setting(settings) -> None:
    settings.MAP_VIEW_URL = "http://localhost:5173/"
    LayerFactory(identifier="trafficsignreal")
    traffic_sign = TrafficSignRealFactory()

    url = build_map_view_inspect_url(traffic_sign)

    assert url == f"http://localhost:5173/?inspect_layer=trafficsignreal&inspect_id={traffic_sign.pk}"


@pytest.mark.django_db
def test_inspect_url_for_mount_uses_centroid_layer() -> None:
    LayerFactory(identifier="mountrealcentroid")
    FeatureTypeEditMappingFactory(name="mountrealcentroid", edit_name="mountreal")
    mount = MountRealFactory()

    query = parse_qs(urlparse(build_map_view_inspect_url(mount)).query)

    assert query == {"inspect_layer": ["mountrealcentroid"], "inspect_id": [str(mount.pk)]}


@pytest.mark.django_db
def test_inspect_url_none_without_layer() -> None:
    assert build_map_view_inspect_url(TrafficSignRealFactory()) is None


@pytest.mark.django_db
def test_inspect_url_none_for_soft_deleted_object() -> None:
    LayerFactory(identifier="trafficsignreal")
    traffic_sign = TrafficSignRealFactory()
    traffic_sign.soft_delete(get_user())
    assert build_map_view_inspect_url(traffic_sign) is None


@pytest.mark.django_db
def test_inspect_url_none_for_unsaved_object() -> None:
    LayerFactory(identifier="trafficsignreal")
    assert build_map_view_inspect_url(TrafficSignReal()) is None


@pytest.mark.parametrize(
    "traffic_sign_kwargs",
    (
        pytest.param({"lifecycle": Lifecycle.INACTIVE}, id="inactive-lifecycle"),
        pytest.param(
            {"validity_period_start": date(2000, 1, 1), "validity_period_end": date(2000, 12, 31)},
            id="expired-validity-period",
        ),
    ),
)
@pytest.mark.django_db
def test_inspect_url_none_when_wfs_does_not_return_object(traffic_sign_kwargs: dict) -> None:
    LayerFactory(identifier="trafficsignreal")
    assert build_map_view_inspect_url(TrafficSignRealFactory(**traffic_sign_kwargs)) is None


@pytest.mark.django_db
def test_inspect_url_none_for_replaced_plan_version() -> None:
    LayerFactory(identifier="trafficsignplan")
    replaced_plan = get_traffic_sign_plan()
    get_traffic_sign_plan(replaces=replaced_plan)

    assert build_map_view_inspect_url(replaced_plan) is None


@pytest.mark.django_db
def test_inspect_url_none_without_wfs_feature_type() -> None:
    barrier = BarrierRealFactory()
    LayerFactory(identifier=barrier._meta.model_name)

    assert build_map_view_inspect_url(barrier) is None
