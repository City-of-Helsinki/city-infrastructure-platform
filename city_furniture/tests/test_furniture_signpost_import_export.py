import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from city_furniture.models import FurnitureSignpostReal
from city_furniture.resources.furniture_signpost import (
    FurnitureSignpostPlanTemplateResource,
    FurnitureSignpostRealResource,
)
from city_furniture.tests.factories import get_furniture_signpost_plan, get_furniture_signpost_real
from traffic_control.enums import OrganizationLevel
from traffic_control.models import GroupResponsibleEntity, ResponsibleEntity
from traffic_control.tests.factories import get_mount_plan, get_mount_real, get_user


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
    dataset.dict = [obj_data]

    result = FurnitureSignpostRealResource().import_data(dataset, raise_errors=True)
    assert not result.has_errors()
    assert FurnitureSignpostReal.objects.all().count() == 1


@pytest.mark.parametrize("has_mount_plan", (True, False), ids=lambda x: "mount_plan" if x else "no_mount_plan")
@pytest.mark.parametrize("has_mount_real", (True, False), ids=lambda x: "mount_real" if x else "no_mount_real")
@pytest.mark.parametrize("real_preexists", (True, False), ids=lambda x: "real_preexists" if x else "real_nonexists")
@pytest.mark.django_db
def test__furniture_signpost_plan_export_real_import(has_mount_plan, has_mount_real, real_preexists):
    """Test that a plan object can be exported using a special resource and then be imported as real"""

    mount_plan = get_mount_plan() if has_mount_plan else None
    mount_real = get_mount_real() if has_mount_real else None

    plan_obj = get_furniture_signpost_plan(mount_plan=mount_plan)
    real_obj = get_furniture_signpost_real(furniture_signpost_plan=plan_obj) if real_preexists else None

    exported_dataset = FurnitureSignpostPlanTemplateResource().export()

    real = exported_dataset.dict[0]
    assert real["furniture_signpost_plan__id"] == plan_obj.id

    if has_mount_plan and has_mount_real:
        assert real["mount_real__id"] == mount_real.id
    else:
        assert real["mount_real__id"] is None

    if real_preexists:
        assert real["id"] == real_obj.id
    else:
        assert real["id"] is None


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
