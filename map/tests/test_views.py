import json

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import override_settings, RequestFactory, TestCase
from django.urls import reverse

from map.models import FeatureTypeEditMapping, IconDrawingConfig, Layer
from map.tests.factories import IconDrawingConfigFactory
from map.views import map_config, map_view
from traffic_control.services.azure import get_azure_icons_base_url
from traffic_control.tests.factories import get_user


class MapViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_redirected_for_non_staff_user(self):
        request = self.factory.get(reverse("map-view"))
        request.user = get_user()
        request.LANGUAGE_CODE = "en"
        response = map_view(request)
        self.assertEqual(response.status_code, 302)

    def test_return_success_for_staff_user(self):
        request = self.factory.get(reverse("map-view"))
        request.user = get_user(admin=True)
        request.LANGUAGE_CODE = "en"
        response = map_view(request)
        self.assertEqual(response.status_code, 200)


@override_settings(
    STORAGES={
        "icons": {
            "OPTIONS": {
                "azure_container": "media",
                "connection_string": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
                "overwrite_files": True,
            }
        }
    }
)
class MapConfigTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.extra_feature_info = {"testfield": {"title_fi": "testi kenttä", "title_en": "test field", "order": 1}}

    def test_with_no_icon_draw_config(self):
        """Test that without any active IconDrawingConfig the default values are used."""
        request = self.factory.get(reverse("map-config"))
        request.LANGUAGE_CODE = "en"

        icon_options = settings.STORAGES["icons"]["OPTIONS"]
        response = map_config(request)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["icon_scale"], IconDrawingConfig.DEFAULT_ICON_SCALE)
        self.assertEqual(response_data["icon_type"], "svg")
        self.assertEqual(
            response_data["traffic_sign_icons_url"],
            f"{get_azure_icons_base_url(icon_options)}icons/traffic_control_device_type/svg/",
        )

    @override_settings(EMULATE_AZURE_BLOBSTORAGE=True)
    def test_with_icon_draw_config(self):
        """Test that with an active IconDrawingConfig the values are actually used."""
        idc = IconDrawingConfigFactory(enabled=True, scale=IconDrawingConfig.DEFAULT_ICON_SCALE + 0.1, image_type="png")
        request = self.factory.get(reverse("map-config"))
        request.LANGUAGE_CODE = "en"

        icon_options = settings.STORAGES["icons"]["OPTIONS"]
        response = map_config(request)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)

        self.assertEqual(response_data["icon_scale"], idc.scale)
        self.assertEqual(response_data["icon_type"], idc.image_type)
        self.assertEqual(
            response_data["traffic_sign_icons_url"],
            f"{get_azure_icons_base_url(icon_options)}icons/traffic_control_device_type/png/{idc.png_size}/",
        )

    def test_layer_config_return_ok_en(self):
        self._do_test_layer_config_ok(
            "en", {"title": self.extra_feature_info.get("testfield").get("title_en"), "order": 1}
        )

    def test_layer_config_return_ok_fi(self):
        self._do_test_layer_config_ok(
            "fi", {"title": self.extra_feature_info.get("testfield").get("title_fi"), "order": 1}
        )

    def test_layer_config_return_ok_sv(self):
        """title_sv is left out from extra_feature_info in purpose to check that fi is selected in this case"""
        self._do_test_layer_config_ok(
            "sv", {"title": self.extra_feature_info.get("testfield").get("title_fi"), "order": 1}
        )

    def test_layer_config_return_ok_not_supported(self):
        self._do_test_layer_config_ok(
            "not_supported_lang",
            {"title": self.extra_feature_info.get("testfield").get("title_fi"), "order": 1},
            "fi",
        )

    def _do_test_layer_config_ok(self, language_code, expected_testfield_info, expected_language_code=None):
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
            extra_feature_info=self.extra_feature_info,
        )
        FeatureTypeEditMapping.objects.create(name="featurename", edit_name="edit_featurename")
        request = self.factory.get(reverse("map-config"))
        request.LANGUAGE_CODE = language_code
        response = map_config(request)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["basemapConfig"]["layers"]), 1)
        self.assertEqual(response_data["basemapConfig"]["layers"][0]["name"], f"Basemap {expect_language_code}")
        self.assertEqual(len(response_data["overlayConfig"]["layers"]), 2)
        self.assertEqual(response_data["overlayConfig"]["layers"][0]["name"], f"Overlay 1 {expect_language_code}")
        self.assertEqual(response_data["overlayConfig"]["layers"][1]["name"], f"Overlay 2 {expect_language_code}")
        self.assertEqual(response_data["overlayConfig"]["layers"][0]["extra_feature_info"], {})
        self.assertEqual(
            response_data["overlayConfig"]["layers"][1]["extra_feature_info"]["testfield"],
            expected_testfield_info,
        )
        self.assertEqual(
            response_data["overviewConfig"]["imageUrl"],
            f"{request.build_absolute_uri(settings.STATIC_URL)}traffic_control/png/map/cityinfra_overview_map-704x704.png",
        )
        self.assertEqual(response_data["overviewConfig"]["imageExtent"], [25490088.0, 6665065.0, 25512616, 6687593.0])
        self.assertEqual(response_data["featureTypeEditNameMapping"], {"featurename": "edit_featurename"})


@pytest.mark.django_db
@pytest.mark.parametrize(
    "extra_feature_info, exception_msg",
    (
        ({"testfield": None}, "Extra Feature Info field data value cannot be empty for key: testfield"),
        ({"testfield": {"title_sv": None}}, "Extra field testfield does not have mandatory value title_fi"),
        (
            {"testfield": {"title_fi": None, "empty_list": [], "empty_dict": {}, "emptry_string": ""}},
            "Extra Feature Info field data cannot be empty:",
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
