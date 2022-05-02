from unittest.mock import Mock

import pytest
from django.core.exceptions import MiddlewareNotUsed
from django.test import override_settings, TestCase

from .middleware import OpenShiftClientIPMiddleware


class OpenShiftClientIPMiddlewareTests(TestCase):
    def setUp(self):
        self.middleware = OpenShiftClientIPMiddleware
        self.request = Mock()
        self.request.META = {}
        self.request.path = "/testURL/"
        self.request.session = {}

    def test__process_request__default(self):
        with pytest.raises(MiddlewareNotUsed):
            self.middleware(get_response=self.request)

    @override_settings(OPENSHIFT_DEPLOYMENT=False)
    def test__process_request__openshift_deployment_false(self):
        with pytest.raises(MiddlewareNotUsed):
            self.middleware(get_response=self.request)

    @override_settings(OPENSHIFT_DEPLOYMENT=True)
    def test__process_request__openshift_deployment_true(self):
        response = self.middleware.process_request(self.request)
        self.assertIsNone(response)

    @override_settings(OPENSHIFT_DEPLOYMENT=True)
    def test__process_request__openshift_deployment_true_ip4(self):
        self.request.META["HTTP_X_FORWARDED_FOR"] = "123.123.123.123"
        self.middleware.process_request(self.request)
        self.assertEqual(self.request.META.get("HTTP_X_FORWARDED_FOR"), "123.123.123.123")

    @override_settings(OPENSHIFT_DEPLOYMENT=True)
    def test__process_request__openshift_deployment_true_ip4_with_port(self):
        self.request.META["HTTP_X_FORWARDED_FOR"] = "123.123.123.123:8000"
        self.middleware.process_request(self.request)
        self.assertEqual(self.request.META.get("HTTP_X_FORWARDED_FOR"), "123.123.123.123")

    @override_settings(OPENSHIFT_DEPLOYMENT=True)
    def test__process_request__openshift_deployment_true_ip4_proxy(self):
        self.request.META["HTTP_X_FORWARDED_FOR"] = "123.123.123.123, 10.10.10.10"
        self.middleware.process_request(self.request)
        self.assertEqual(self.request.META.get("HTTP_X_FORWARDED_FOR"), "123.123.123.123")

    @override_settings(OPENSHIFT_DEPLOYMENT=True)
    def test__process_request__openshift_deployment_true_ip4_with_port_proxy(self):
        self.request.META["HTTP_X_FORWARDED_FOR"] = "123.123.123.123:8000, 10.10.10.10"
        self.middleware.process_request(self.request)
        self.assertEqual(self.request.META.get("HTTP_X_FORWARDED_FOR"), "123.123.123.123")

    @override_settings(OPENSHIFT_DEPLOYMENT=True)
    def test__process_request__openshift_deployment_true_ip4_with_port_proxy_port(self):
        self.request.META["HTTP_X_FORWARDED_FOR"] = "123.123.123.123:8000, 10.10.10.10:9999"
        self.middleware.process_request(self.request)
        self.assertEqual(self.request.META.get("HTTP_X_FORWARDED_FOR"), "123.123.123.123")

    @override_settings(OPENSHIFT_DEPLOYMENT=True)
    def test__process_request__openshift_deployment_true_ip6(self):
        self.request.META["HTTP_X_FORWARDED_FOR"] = "2001:db8::8a2e:370:7334"
        self.middleware.process_request(self.request)
        self.assertEqual(self.request.META.get("HTTP_X_FORWARDED_FOR"), "2001:db8::8a2e:370:7334")

    @override_settings(OPENSHIFT_DEPLOYMENT=True)
    def test__process_request__openshift_deployment_true_invalid_ip(self):
        self.request.META["HTTP_X_FORWARDED_FOR"] = "abc"
        with pytest.raises(ValueError):
            self.middleware.process_request(self.request)
