from unittest.mock import Mock

import pytest
from django.core.exceptions import MiddlewareNotUsed
from django.test import override_settings, TestCase

from .middleware import AzureClientIPMiddleware


class AzureClientIPMiddlewareTests(TestCase):
    def setUp(self):
        self.middleware = AzureClientIPMiddleware
        self.request = Mock()
        self.request.META = {
            "HTTP_X_CLIENT_IP": "123.123.123.123:8080",
        }
        self.request.path = "/testURL/"
        self.request.session = {}

    def test__process_request__default(self):
        with pytest.raises(MiddlewareNotUsed):
            self.middleware(get_response=self.request)

    @override_settings(AZURE_DEPLOYMENT=False)
    def test__process_request__azure_deployment_false(self):
        with pytest.raises(MiddlewareNotUsed):
            self.middleware(get_response=self.request)

    @override_settings(AZURE_DEPLOYMENT=True)
    def test__process_request__azure_deployment_true(self):
        response = self.middleware.process_request(self.request)
        self.assertIsNone(response)
        self.assertEqual(
            self.request.META.get("HTTP_X_FORWARDED_FOR"),
            self.request.META.get("HTTP_X_CLIENT_IP"),
        )
