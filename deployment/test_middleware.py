from rest_framework import status
from rest_framework.test import APITestCase


class HealthTests(APITestCase):
    def test_healthz_ok(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, b"OK")

    def test_readiness_ok(self):
        response = self.client.get("/readiness")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, b"OK")
