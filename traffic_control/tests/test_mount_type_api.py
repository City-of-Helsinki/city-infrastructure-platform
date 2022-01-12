from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import MountType

User = get_user_model()


class MountTypeTests(APITestCase):
    def setUp(self):
        MountType.objects.all().delete()
        self.admin_user = User.objects.create_superuser(username="admin", password="admin", email="admin@example.com")
        self.user = User.objects.create_user(username="user", password="user")

    def test__list__as_user__ok(self):
        self.client.force_login(self.user)
        types = ["post", "wall", "wire"]
        for t in types:
            MountType.objects.create(code=t.upper(), description=t.capitalize())
        response = self.client.get(reverse("v1:mounttype-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), len(types))

    def test__get_list__as_admin__ok(self):
        self.client.force_login(self.admin_user)
        types = ["post", "wall", "wire"]
        for t in types:
            MountType.objects.create(code=t.upper(), description=t.capitalize())
        response = self.client.get(reverse("v1:mounttype-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), len(types))

    def test__retrieve__as_user__ok(self):
        self.client.force_login(self.user)
        mount_type = self.__create_test_mount_type()
        response = self.client.get(reverse("v1:mounttype-detail", kwargs={"pk": mount_type.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(mount_type.id))

    def test__retrieve__as_admin__ok(self):
        self.client.force_login(self.admin_user)
        mount_type = self.__create_test_mount_type()
        response = self.client.get(reverse("v1:mounttype-detail", kwargs={"pk": mount_type.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(mount_type.id))

    def test__create__as_user__forbidden(self):
        self.client.force_login(self.user)
        data = {"code": "POST", "description": "Post"}
        response = self.client.post(reverse("v1:mounttype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(MountType.objects.count(), 0)

    def test__create__as_admin__created(self):
        self.client.force_login(self.admin_user)
        data = {"code": "POST", "description": "Post"}
        response = self.client.post(reverse("v1:mounttype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MountType.objects.count(), 1)
        mount_type = MountType.objects.first()
        self.assertEqual(mount_type.code, data["code"])
        self.assertEqual(mount_type.description, data["description"])
        self.assertEqual(mount_type.digiroad_code, None)
        self.assertEqual(mount_type.digiroad_description, "")

    def test__update__as_user__forbidden(self):
        self.client.force_login(self.user)
        mount_type = self.__create_test_mount_type()
        data = {"code": "POST", "description": "Post"}
        response = self.client.put(
            reverse("v1:mounttype-detail", kwargs={"pk": mount_type.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test__update__as_admin__ok(self):
        self.client.force_login(self.admin_user)
        mount_type = self.__create_test_mount_type()
        data = {"code": "POST", "description": "Post"}
        response = self.client.put(
            reverse("v1:mounttype-detail", kwargs={"pk": mount_type.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(MountType.objects.count(), 1)
        mount_type = MountType.objects.first()
        self.assertEqual(mount_type.code, data["code"])
        self.assertEqual(mount_type.description, data["description"])

    def test__destroy__as_user__forbidden(self):
        self.client.force_login(self.user)
        mount_type = self.__create_test_mount_type()
        response = self.client.delete(
            reverse("v1:mounttype-detail", kwargs={"pk": mount_type.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(MountType.objects.count(), 1)

    def test__destroy__as_admin__success(self):
        self.client.force_login(self.admin_user)
        mount_type = self.__create_test_mount_type()
        response = self.client.delete(
            reverse("v1:mounttype-detail", kwargs={"pk": mount_type.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(MountType.objects.count(), 0)

    @staticmethod
    def __create_test_mount_type():
        return MountType.objects.create(code="POST", description="Post")
