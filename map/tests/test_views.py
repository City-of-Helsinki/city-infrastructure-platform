from django.test import override_settings, RequestFactory, TestCase
from django.urls import reverse

from map.views import map_view
from traffic_control.tests.factories import get_user


@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
)
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
