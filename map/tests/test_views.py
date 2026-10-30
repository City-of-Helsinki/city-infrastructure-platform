import json

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from map.models import FeatureTypeEditMapping, IconDrawingConfig, Layer
from map.tests.factories import IconDrawingConfigFactory
from map.views import map_config
from traffic_control.services.azure import get_azure_storage_base_url


@pytest.fixture(autouse=True)
def settings(settings):
    settings.EMULATE_AZURE_BLOBSTORAGE = True
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "icons": {
            # "BACKEND": "cityinfra.storages.backends.non_leaky_azure_storage.NonLeakyAzureStorage",
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {
                "azure_container": "media",
                "connection_string": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",  # noqa: E501
                "overwrite_files": True,
            },
        },
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    return settings


extra_feature_info = {"testfield": {"title_fi": "testi kenttä", "title_en": "test field", "order": 1}}


@pytest.mark.django_db
def test_redirected_for_non_staff_user(client):
    response = client.get(reverse("map-view"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_return_success_for_staff_user(admin_client):
    response = admin_client.get(reverse("map-view"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_with_no_icon_draw_config(client, settings):
    """Test that without any active IconDrawingConfig the default values are used."""
    icon_options = settings.STORAGES["icons"]["OPTIONS"]
    response = client.get(reverse("map-config"))
    assert response.status_code == 200
    response_data = json.loads(response.content)
    assert response_data["icon_scale"] == IconDrawingConfig.DEFAULT_ICON_SCALE
    assert response_data["icon_type"] == "svg"
    assert response_data["icon_size"] == IconDrawingConfig.DEFAULT_ICON_SIZE
    assert (
        response_data["traffic_sign_icons_url"]
        == f"{get_azure_storage_base_url(icon_options)}icons/traffic_control_device_type/svg/"
    )


@pytest.mark.django_db
def test_with_icon_draw_config(client, settings):
    """Test that with an active IconDrawingConfig the values are actually used."""
    idc = IconDrawingConfigFactory(
        enabled=True, scale=IconDrawingConfig.DEFAULT_ICON_SCALE + 0.1, image_type="png", png_size=128
    )

    icon_options = settings.STORAGES["icons"]["OPTIONS"]
    response = client.get(reverse("map-config"))
    assert response.status_code == 200
    response_data = json.loads(response.content)

    assert response_data["icon_scale"] == idc.scale
    assert response_data["icon_type"] == idc.image_type
    assert response_data["icon_size"] == idc.png_size
    assert (
        response_data["traffic_sign_icons_url"]
        == f"{get_azure_storage_base_url(icon_options)}icons/traffic_control_device_type/png/{idc.png_size}/"
    )


@pytest.mark.django_db
def test_layer_config_return_ok_en(rf, settings):
    _do_test_layer_config_ok(
        rf, settings, "en", {"title": extra_feature_info.get("testfield").get("title_en"), "order": 1}
    )


@pytest.mark.django_db
def test_layer_config_return_ok_fi(rf, settings):
    _do_test_layer_config_ok(
        rf, settings, "fi", {"title": extra_feature_info.get("testfield").get("title_fi"), "order": 1}
    )


@pytest.mark.django_db
def test_layer_config_return_ok_sv(rf, settings):
    """title_sv is left out from extra_feature_info in purpose to check that fi is selected in this case"""
    _do_test_layer_config_ok(
        rf, settings, "sv", {"title": extra_feature_info.get("testfield").get("title_fi"), "order": 1}
    )


@pytest.mark.django_db
def test_layer_config_return_ok_not_supported(rf, settings):
    _do_test_layer_config_ok(
        rf,
        settings,
        "not_supported_lang",
        {"title": extra_feature_info.get("testfield").get("title_fi"), "order": 1},
        "fi",
    )


def _do_test_layer_config_ok(rf, settings, language_code, expected_testfield_info, expected_language_code=None):
    expect_language_code = expected_language_code or language_code
    Layer.objects.create(
        identifier="basemap",
        name_en="Basemap en",
        name_fi="Basemap fi",
        name_sv="Basemap sv",
        is_basemap=True,
    )
    Layer.objects.create(
        identifier="overlay-1",
        name_en="Overlay 1 en",
        name_fi="Overlay 1 fi",
        name_sv="Overlay 1 sv",
        is_basemap=False,
    )
    Layer.objects.create(
        identifier="overlay-2",
        name_en="Overlay 2 en",
        name_fi="Overlay 2 fi",
        name_sv="Overlay 2 sv",
        is_basemap=False,
        extra_feature_info=extra_feature_info,
    )
    FeatureTypeEditMapping.objects.create(name="featurename", edit_name="edit_featurename")
    request = rf.get(reverse("map-config"))
    request.LANGUAGE_CODE = language_code
    response = map_config(request)
    assert response.status_code == 200
    response_data = json.loads(response.content)

    assert len(response_data["basemapConfig"]["layers"]) == 1
    assert response_data["basemapConfig"]["layers"][0]["name"] == f"Basemap {expect_language_code}"
    assert len(response_data["overlayConfig"]["layers"]) == 2
    assert response_data["overlayConfig"]["layers"][0]["name"] == f"Overlay 1 {expect_language_code}"
    assert response_data["overlayConfig"]["layers"][1]["name"] == f"Overlay 2 {expect_language_code}"
    assert response_data["overlayConfig"]["layers"][0]["extra_feature_info"] == {}
    assert response_data["overlayConfig"]["layers"][1]["extra_feature_info"]["testfield"] == expected_testfield_info
    assert (
        response_data["overviewConfig"]["imageUrl"]
        == f"{request.build_absolute_uri(settings.STATIC_URL)}traffic_control/png/map/cityinfra_overview_map-704x704.png"  # noqa: E501
    )
    assert response_data["overviewConfig"]["imageExtent"] == [25490088.0, 6665065.0, 25512616, 6687593.0]
    assert response_data["featureTypeEditNameMapping"] == {"featurename": "edit_featurename"}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "extra_feature_info, exception_msg",
    (
        ({"testfield": None}, "Extra feature info field data value cannot be empty for key: testfield"),
        ({"testfield": {"title_sv": None}}, "Extra field testfield does not have mandatory value title_fi"),
        (
            {"testfield": {"title_fi": None, "empty_list": [], "empty_dict": {}, "emptry_string": ""}},
            "Extra feature info field data cannot be empty:",
        ),
    ),
)
def test_extra_feature_info_not_ok(extra_feature_info, exception_msg):
    layer = Layer(
        identifier="overlay-1",
        name_en="Overlay 1 en",
        name_fi="Overlay 1 fi",
        name_sv="Overlay 1 sv",
        is_basemap=False,
        extra_feature_info=extra_feature_info,
    )
    with pytest.raises(ValidationError) as exc_info:
        # full_clean has to be called so field validators are called.
        layer.full_clean()
    assert exc_info.value is not None
    assert "extra_feature_info" in exc_info.value.error_dict
    assert exception_msg in exc_info.value.error_dict.get("extra_feature_info", [])[0].messages[0]
