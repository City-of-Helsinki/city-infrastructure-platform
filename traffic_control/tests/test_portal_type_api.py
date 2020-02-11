from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from traffic_control.models import PortalType
from users.models import User


class PortalTypeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="testadmin", password="testpw", email="testadmin@anders.fi"
        )
        self.client.login(username="testadmin", password="testpw")

    def test_get_all_portal_types(self):
        """
        Ensure we can get all portal type objects.
        """
        count = 3
        for i in range(count):
            PortalType.objects.create(
                structure="Test structure", build_type="Test build type", model=i
            )
        response = self.client.get(reverse("api:portaltype-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test_get_portal_type_detail(self):
        """
        Ensure we can get one portal type object.
        """
        portal_type = self.__create_test_portal_type()
        response = self.client.get(
            reverse("api:portaltype-detail", kwargs={"pk": portal_type.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(portal_type.id))

    def test_create_portal_type(self):
        """
        Ensure we can create a new portal type object.
        """
        data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
        response = self.client.post(reverse("api:portaltype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PortalType.objects.count(), 1)
        portal_type = PortalType.objects.first()
        self.assertEqual(portal_type.structure, data["structure"])
        self.assertEqual(portal_type.build_type, data["build_type"])
        self.assertEqual(portal_type.model, data["model"])

    def test_create_existing_portal_type(self):
        """
        Ensure that we cannot create a new portal type object with same values.
        """
        data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
        response = self.client.post(reverse("api:portaltype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(reverse("api:portaltype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PortalType.objects.count(), 1)
        portal_type = PortalType.objects.first()
        self.assertEqual(portal_type.structure, data["structure"])
        self.assertEqual(portal_type.build_type, data["build_type"])
        self.assertEqual(portal_type.model, data["model"])

    def test_update_portal_type(self):
        """
        Ensure we can update existing portal type object.
        """
        portal_type = self.__create_test_portal_type()
        data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
        response = self.client.put(
            reverse("api:portaltype-detail", kwargs={"pk": portal_type.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(PortalType.objects.count(), 1)
        portal_type = PortalType.objects.first()
        self.assertEqual(portal_type.structure, data["structure"])
        self.assertEqual(portal_type.build_type, data["build_type"])
        self.assertEqual(portal_type.model, data["model"])

    def test_delete_portal_type_detail(self):
        """
        Ensure we can delete one portal type object.
        """
        portal_type = self.__create_test_portal_type()
        response = self.client.delete(
            reverse("api:portaltype-detail", kwargs={"pk": portal_type.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PortalType.objects.count(), 0)

    def __create_test_portal_type(self):
        return PortalType.objects.create(
            structure="Test structure", build_type="Test build type", model="Test model"
        )
