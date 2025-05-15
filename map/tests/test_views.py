import json

from django.conf import settings
from django.test import RequestFactory, TestCase
from django.urls import reverse

from map.models import FeatureTypeEditMapping, Layer
from map.views import map_config, map_view
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


class MapConfigTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_layer_config_return_ok(self):
        Layer.objects.create(
            identifier="basemap",
            name_en="Basemap en",
            name_fi="Basemap fi",
            is_basemap=True,
        )
        Layer.objects.create(
            identifier="overlay-1",
            name_en="Overlay 1 en",
            name_fi="Overlay 1 fi",
            is_basemap=False,
        )
        Layer.objects.create(
            identifier="overlay-2",
            name_en="Overlay 2 en",
            name_fi="Overlay 2 fi",
            is_basemap=False,
        )
        FeatureTypeEditMapping.objects.create(name="featurename", edit_name="edit_featurename")
        request = self.factory.get(reverse("map-config"))
        request.LANGUAGE_CODE = "en"
        response = map_config(request)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["basemapConfig"]["layers"]), 1)
        self.assertEqual(len(response_data["overlayConfig"]["layers"]), 2)
        self.assertEqual(
            response_data["overviewConfig"]["imageUrl"],
            f"{request.build_absolute_uri(settings.STATIC_URL)}traffic_control/png/map/cityinfra_overview_map-704x704.png",
        )
        self.assertEqual(response_data["overviewConfig"]["imageExtent"], [25490088.0, 6665065.0, 25512616, 6687593.0])
        self.assertEqual(response_data["featureTypeEditNameMapping"], {"featurename": "edit_featurename"})
