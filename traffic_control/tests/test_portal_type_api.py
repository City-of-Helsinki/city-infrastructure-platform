from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from traffic_control.models import PortalType
from users.models import User


class PortalTypeTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="testadmin", password="testpw", email="testadmin@anders.fi"
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
            PortalType.objects.create(
                structure="Test structure", build_type="Test build type", model=i
            )
        response = self.client.get(reverse("api:portaltype-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test__get_list__as_admin__ok(self):
        """
        Ensure that admin can get list of portal type objects.
        """
        self.client.force_login(self.admin_user)
        count = 3
        for i in range(count):
            PortalType.objects.create(
                structure="Test structure", build_type="Test build type", model=i
            )
        response = self.client.get(reverse("api:portaltype-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test__retrieve__as_user__ok(self):
        """
        Ensure that user can get portal type object.
        """
        self.client.force_login(self.user)
        portal_type = self.__create_test_portal_type()
        response = self.client.get(
            reverse("api:portaltype-detail", kwargs={"pk": portal_type.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(portal_type.id))

    def test__retrieve__as_admin__ok(self):
        """
        Ensure that admin can get portal type object.
        """
        self.client.force_login(self.admin_user)
        portal_type = self.__create_test_portal_type()
        response = self.client.get(
            reverse("api:portaltype-detail", kwargs={"pk": portal_type.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(portal_type.id))

    def test__create__as_user__forbidden(self):
        """
        Ensure that user cannot create a new portal type object.
        """
        self.client.force_login(self.user)
        data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
        response = self.client.post(reverse("api:portaltype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PortalType.objects.count(), 0)

    def test__create__as_admin__created(self):
        """
        Ensure that admin can create a new portal type object.
        """
        self.client.force_login(self.admin_user)
        data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
        response = self.client.post(reverse("api:portaltype-list"), data, format="json")
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
        response = self.client.post(reverse("api:portaltype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(reverse("api:portaltype-list"), data, format="json")
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
            reverse("api:portaltype-detail", kwargs={"pk": portal_type.id}),
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

    def test__destroy__as_user__forbidden(self):
        """
        Ensure that user cannot destroy portal type object.
        """
        self.client.force_login(self.user)
        portal_type = self.__create_test_portal_type()
        response = self.client.delete(
            reverse("api:portaltype-detail", kwargs={"pk": portal_type.id}),
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
            reverse("api:portaltype-detail", kwargs={"pk": portal_type.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PortalType.objects.count(), 0)

    @staticmethod
    def __create_test_portal_type():
        return PortalType.objects.create(
            structure="Test structure", build_type="Test build type", model="Test model"
        )
