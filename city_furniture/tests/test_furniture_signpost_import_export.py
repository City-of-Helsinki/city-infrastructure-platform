import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from city_furniture.enums import OrganizationLevel
from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal, ResponsibleEntity
from city_furniture.models.responsible_entity import GroupResponsibleEntity
from city_furniture.resources.furniture_signpost import (
    FurnitureSignpostPlanTemplateResource,
    FurnitureSignpostRealResource,
)
from city_furniture.tests.factories import get_furniture_signpost_plan, get_furniture_signpost_real
from traffic_control.tests.factories import get_user


@pytest.mark.django_db
def test__furniture_signpost_real__export():
    fsr = get_furniture_signpost_real()

    dataset = FurnitureSignpostRealResource().export()

    assert dataset.dict[0]["location"] == str(fsr.location)
    assert dataset.dict[0]["owner__name_fi"] == fsr.owner.name_fi
    assert dataset.dict[0]["device_type__code"] == fsr.device_type.code
    assert dataset.dict[0]["lifecycle"] == fsr.lifecycle.name


@pytest.mark.django_db
def test__furniture_signpost_real__import():
    get_furniture_signpost_real()  # Create a furniture signpost so we can easily populate the data
    dataset = FurnitureSignpostRealResource().export()
    FurnitureSignpostReal.objects.all().delete()

    # Remove ID from data to create new objects
    obj_data = dataset.dict[0]
    obj_data.pop("id")
    dataset.dict[0] = obj_data

    result = FurnitureSignpostRealResource().import_data(dataset, raise_errors=True)
    assert not result.has_errors()
    assert FurnitureSignpostReal.objects.all().count() == 1


@pytest.mark.django_db
def test__furniture_signpost_plan_export_real_import():
    """Test that a plan object can be exported using a special resource and then be imported as real"""

    get_furniture_signpost_plan()
    dataset = FurnitureSignpostPlanTemplateResource().export()

    result = FurnitureSignpostRealResource().import_data(dataset, raise_errors=True)
    assert not result.has_errors()
    assert FurnitureSignpostPlan.objects.all().count() == 1
    assert FurnitureSignpostReal.objects.all().count() == 1
    assert FurnitureSignpostReal.objects.first().furniture_signpost_plan_id == FurnitureSignpostPlan.objects.first().id


@pytest.mark.django_db
def test__furniture_signpost_real__import__responsible_entity_permission():
    get_furniture_signpost_real()
    dataset = FurnitureSignpostRealResource().export()

    user = get_user()
    with pytest.raises(ValidationError):
        FurnitureSignpostRealResource().import_data(dataset, raise_errors=True, user=user)

    user.responsible_entities.add(ResponsibleEntity.objects.get(organization_level=OrganizationLevel.PROJECT))
    result = FurnitureSignpostRealResource().import_data(dataset, raise_errors=True, user=user)
    assert not result.has_errors()

    user.responsible_entities.clear()
    user.responsible_entities.add(ResponsibleEntity.objects.get(organization_level=OrganizationLevel.DIVISION))
    result = FurnitureSignpostRealResource().import_data(dataset, raise_errors=True, user=user)
    assert not result.has_errors()


@pytest.mark.django_db
def test__furniture_signpost_real__import__responsible_entity_permission__group():
    get_furniture_signpost_real()
    dataset = FurnitureSignpostRealResource().export()

    user = get_user()
    with pytest.raises(ValidationError):
        FurnitureSignpostRealResource().import_data(dataset, raise_errors=True, user=user)

    group = Group.objects.create(name="test group")
    user.groups.add(group)
    gre = GroupResponsibleEntity.objects.create(group=group)
    gre.responsible_entities.add(ResponsibleEntity.objects.get(organization_level=OrganizationLevel.PROJECT))
    result = FurnitureSignpostRealResource().import_data(dataset, raise_errors=True, user=user)
    assert not result.has_errors()

    gre.responsible_entities.clear()
    gre.responsible_entities.add(ResponsibleEntity.objects.get(organization_level=OrganizationLevel.DIVISION))
    result = FurnitureSignpostRealResource().import_data(dataset, raise_errors=True, user=user)
    assert not result.has_errors()


@pytest.mark.django_db
def test__furniture_signpost_real__import__responsible_entity_permission_bypass():
    get_furniture_signpost_real()
    dataset = FurnitureSignpostRealResource().export()

    user = get_user()
    user.bypass_responsible_entity = True
    user.save()

    result = FurnitureSignpostRealResource().import_data(dataset, raise_errors=True, user=user)
    assert not result.has_errors()
