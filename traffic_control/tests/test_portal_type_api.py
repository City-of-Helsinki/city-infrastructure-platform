import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from traffic_control.models import PortalType
from traffic_control.tests.factories import get_api_client, get_portal_type
from users.models import User


class PortalTypeTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="testadmin", password="testpw", email="testadmin@hel.fi"
        )
        self.user = User.objects.create_user(username="testuser", password="testpw")
        self.client.login(username="testadmin", password="testpw")

    def test__list__as_user__ok(self):
        """
        Ensure that user can get list of portal type objects.
        """
        self.client.force_login(self.user)
        count = 3
        for i in range(count):
            PortalType.objects.create(structure="Test structure", build_type="Test build type", model=i)
        response = self.client.get(reverse("v1:portaltype-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test__get_list__as_admin__ok(self):
        """
        Ensure that admin can get list of portal type objects.
        """
        self.client.force_login(self.admin_user)
        count = 3
        for i in range(count):
            PortalType.objects.create(structure="Test structure", build_type="Test build type", model=i)
        response = self.client.get(reverse("v1:portaltype-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test__retrieve__as_user__ok(self):
        """
        Ensure that user can get portal type object.
        """
        self.client.force_login(self.user)
        portal_type = self.__create_test_portal_type()
        response = self.client.get(reverse("v1:portaltype-detail", kwargs={"pk": portal_type.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(portal_type.id))

    def test__retrieve__as_admin__ok(self):
        """
        Ensure that admin can get portal type object.
        """
        self.client.force_login(self.admin_user)
        portal_type = self.__create_test_portal_type()
        response = self.client.get(reverse("v1:portaltype-detail", kwargs={"pk": portal_type.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(portal_type.id))

    def test__create__as_user__forbidden(self):
        """
        Ensure that user cannot create a new portal type object.
        """
        self.client.force_login(self.user)
        data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
        response = self.client.post(reverse("v1:portaltype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PortalType.objects.count(), 0)

    def test__create__as_admin__created(self):
        """
        Ensure that admin can create a new portal type object.
        """
        self.client.force_login(self.admin_user)
        data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
        response = self.client.post(reverse("v1:portaltype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PortalType.objects.count(), 1)
        portal_type = PortalType.objects.first()
        self.assertEqual(portal_type.structure, data["structure"])
        self.assertEqual(portal_type.build_type, data["build_type"])
        self.assertEqual(portal_type.model, data["model"])

    def test__create_existing__bad_request(self):
        """
        Ensure that API will not create a new portal type object with same values.
        """
        data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
        response = self.client.post(reverse("v1:portaltype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(reverse("v1:portaltype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PortalType.objects.count(), 1)
        portal_type = PortalType.objects.first()
        self.assertEqual(portal_type.structure, data["structure"])
        self.assertEqual(portal_type.build_type, data["build_type"])
        self.assertEqual(portal_type.model, data["model"])

    def test__update__as_user__forbidden(self):
        """
        Ensure that user cannot update existing portal type object.
        """
        self.client.force_login(self.user)
        portal_type = self.__create_test_portal_type()
        data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
        response = self.client.put(
            reverse("v1:portaltype-detail", kwargs={"pk": portal_type.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test__update__as_admin__ok(self):
        """
        Ensure that admin can update existing portal type object.
        """
        self.client.force_login(self.admin_user)
        portal_type = self.__create_test_portal_type()
        data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
        response = self.client.put(
            reverse("v1:portaltype-detail", kwargs={"pk": portal_type.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(PortalType.objects.count(), 1)
        portal_type = PortalType.objects.first()
        self.assertEqual(portal_type.structure, data["structure"])
        self.assertEqual(portal_type.build_type, data["build_type"])
        self.assertEqual(portal_type.model, data["model"])

    def test__destroy__as_user__forbidden(self):
        """
        Ensure that user cannot destroy portal type object.
        """
        self.client.force_login(self.user)
        portal_type = self.__create_test_portal_type()
        response = self.client.delete(
            reverse("v1:portaltype-detail", kwargs={"pk": portal_type.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PortalType.objects.count(), 1)

    def test__destroy__as_admin__success(self):
        """
        Ensure that admin can delete portal type object.
        """
        self.client.force_login(self.admin_user)
        portal_type = self.__create_test_portal_type()
        response = self.client.delete(
            reverse("v1:portaltype-detail", kwargs={"pk": portal_type.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PortalType.objects.count(), 0)

    @staticmethod
    def __create_test_portal_type():
        return PortalType.objects.create(structure="Test structure", build_type="Test build type", model="Test model")


@pytest.mark.parametrize(
    "method, expected_status",
    (
        ("GET", status.HTTP_200_OK),
        ("HEAD", status.HTTP_200_OK),
        ("OPTIONS", status.HTTP_200_OK),
        ("POST", status.HTTP_401_UNAUTHORIZED),
        ("PUT", status.HTTP_401_UNAUTHORIZED),
        ("PATCH", status.HTTP_401_UNAUTHORIZED),
        ("DELETE", status.HTTP_401_UNAUTHORIZED),
    ),
)
@pytest.mark.parametrize("view_type", ("detail", "list"))
@pytest.mark.django_db
def test__portal_type__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    portal_type = get_portal_type(
        model="Model 1",
        build_type="Build type 1",
        structure="Structure 1",
    )
    kwargs = {"pk": portal_type.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:portaltype-{view_type}", kwargs=kwargs)
    data = {
        "structure": "Structure 2",
        "build_type": "Build type 2",
        "model": "Model 2",
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert PortalType.objects.count() == 1
    assert PortalType.objects.first().model == "Model 1"
    assert response.status_code == expected_status
