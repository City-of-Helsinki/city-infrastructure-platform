import pytest
from django.urls import reverse
from rest_framework import status

from traffic_control.models import Owner
from traffic_control.tests.factories import get_api_client, get_owner, get_user


@pytest.mark.django_db
@pytest.mark.parametrize("is_admin", (True, False))
def test__owner_api__list(is_admin):
    Owner.objects.all().delete()
    user = get_user(admin=is_admin)
    client = get_api_client(user)
    get_owner(name_fi="owner 1")
    get_owner(name_fi="owner 2")

    response = client.get(reverse("v1:owner-list"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 2


@pytest.mark.django_db
@pytest.mark.parametrize("is_admin", (True, False))
def test__owner_api__retrieve(is_admin):
    Owner.objects.all().delete()
    user = get_user(admin=is_admin)
    client = get_api_client(user)
    owner_1 = get_owner(name_fi="owner 1")
    get_owner(name_fi="owner 2")

    response = client.get(reverse("v1:owner-detail", kwargs={"pk": owner_1.pk}))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == str(owner_1.pk)
    assert response.data["name_fi"] == owner_1.name_fi


@pytest.mark.django_db
@pytest.mark.parametrize("is_admin", (True, False))
def test__owner_api__create(is_admin):
    Owner.objects.all().delete()
    user = get_user(admin=is_admin)
    client = get_api_client(user)
    data = {
        "name_fi": "Omistajan nimi",
        "name_en": "Owner name",
    }

    response = client.post(reverse("v1:owner-list"), data=data)

    if is_admin:
        owner = Owner.objects.first()
        assert response.status_code == status.HTTP_201_CREATED
        assert Owner.objects.count() == 1
        assert owner.name_fi == data["name_fi"]
        assert owner.name_en == data["name_en"]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Owner.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("is_admin", (True, False))
def test__owner_api__update(is_admin):
    Owner.objects.all().delete()
    user = get_user(admin=is_admin)
    client = get_api_client(user)
    owner = get_owner(name_fi="foo", name_en="bar")
    data = {
        "name_fi": "Omistajan nimi",
        "name_en": "Owner name",
    }

    response = client.put(
        reverse("v1:owner-detail", kwargs={"pk": owner.pk}), data=data
    )
    owner.refresh_from_db()
    assert Owner.objects.count() == 1

    if is_admin:
        assert response.status_code == status.HTTP_200_OK
        assert owner.name_fi == data["name_fi"]
        assert owner.name_en == data["name_en"]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert owner.name_fi == "foo"
        assert owner.name_en == "bar"


@pytest.mark.django_db
@pytest.mark.parametrize("is_admin", (True, False))
def test__owner_api__partial_update(is_admin):
    Owner.objects.all().delete()
    user = get_user(admin=is_admin)
    client = get_api_client(user)
    owner = get_owner(name_fi="foo", name_en="bar")
    data = {
        "name_fi": "Omistajan nimi",
    }

    response = client.patch(
        reverse("v1:owner-detail", kwargs={"pk": owner.pk}), data=data
    )
    owner.refresh_from_db()
    assert Owner.objects.count() == 1

    if is_admin:
        assert response.status_code == status.HTTP_200_OK
        assert owner.name_fi == data["name_fi"]
        assert owner.name_en == "bar"
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert owner.name_fi == "foo"
        assert owner.name_en == "bar"


@pytest.mark.django_db
@pytest.mark.parametrize("is_admin", (True, False))
def test__owner_api__destroy(is_admin):
    Owner.objects.all().delete()
    user = get_user(admin=is_admin)
    client = get_api_client(user)
    owner = get_owner(name_fi="foo", name_en="bar")

    response = client.delete(reverse("v1:owner-detail", kwargs={"pk": owner.pk}))

    if is_admin:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Owner.objects.count() == 0
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Owner.objects.count() == 1
