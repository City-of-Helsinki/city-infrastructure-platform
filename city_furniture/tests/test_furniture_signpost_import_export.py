from uuid import UUID

import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.resources.furniture_signpost import (
    FurnitureSignpostPlanResource,
    FurnitureSignpostPlanTemplateResource,
    FurnitureSignpostRealResource,
)
from city_furniture.tests.factories import get_furniture_signpost_plan, get_furniture_signpost_real
from traffic_control.enums import OrganizationLevel
from traffic_control.models import GroupResponsibleEntity, ResponsibleEntity
from traffic_control.tests.factories import get_mount_plan, get_mount_real, get_responsible_entity_project, get_user
from traffic_control.tests.test_base_api import test_point_2
from traffic_control.tests.test_import_export.utils import file_formats, get_import_dataset


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
@pytest.mark.parametrize("has_parent_plan", (True, False), ids=lambda x: "parent_plan" if x else "no_parent_plan")
@pytest.mark.parametrize("has_parent_real", (True, False), ids=lambda x: "parent_real" if x else "no_parent_real")
@pytest.mark.parametrize("real_preexists", (True, False), ids=lambda x: "real_preexists" if x else "real_nonexists")
@pytest.mark.django_db
def test__furniture_signpost_plan_export_real(
    has_mount_plan,
    has_mount_real,
    has_parent_plan,
    has_parent_real,
    real_preexists,
):
    """Test that a plan object can be exported as its real object (referencing to the plan)"""

    mount_plan = get_mount_plan() if has_mount_plan else None
    mount_real = get_mount_real() if has_mount_real else None
    parent_plan = get_furniture_signpost_plan() if has_parent_plan else None
    parent_real = get_furniture_signpost_real(furniture_signpost_plan=parent_plan) if has_parent_real else None

    plan_obj = get_furniture_signpost_plan(
        location=test_point_2,
        mount_plan=mount_plan,
        parent=parent_plan,
    )
    real_obj = (
        get_furniture_signpost_real(
            location=test_point_2,
            furniture_signpost_plan=plan_obj,
            parent=parent_real,
        )
        if real_preexists
        else None
    )

    exported_dataset = FurnitureSignpostPlanTemplateResource().export(
        queryset=FurnitureSignpostPlan.objects.filter(id=plan_obj.id)
    )
    assert len(exported_dataset) == 1

    real = exported_dataset.dict[0]
    assert real["furniture_signpost_plan__id"] == plan_obj.id

    if has_mount_plan and has_mount_real:
        assert real["mount_real__id"] == mount_real.id
    else:
        assert real["mount_real__id"] is None

    if has_parent_plan:
        if has_parent_real:
            assert real["parent__id"] == parent_real.id
        else:
            if real_preexists:
                assert real["parent__id"] == 1
            else:
                assert real["parent__id"] == 1
    else:
        assert real["parent__id"] is None

    if real_preexists:
        assert real["id"] == real_obj.id
    else:
        assert real["id"] is None


@pytest.mark.django_db
def test__furniture_signpost_plan_export_real_replacement_importable():
    """
    Test that a plan objects can be exported to real objects with parent-child id replacements
    and the result is importable.
    """

    get_furniture_signpost_plan(location_name_en="A")
    plan_b = get_furniture_signpost_plan(location_name_en="B")
    get_furniture_signpost_plan(location_name_en="C", parent=plan_b)
    plan_d = get_furniture_signpost_plan(location_name_en="D", parent=plan_b)
    get_furniture_signpost_plan(location_name_en="E", parent=plan_d)

    exported_dataset = FurnitureSignpostPlanTemplateResource().export()
    assert len(exported_dataset) == 5

    import_result = FurnitureSignpostRealResource().import_data(exported_dataset, raise_errors=False)
    assert not import_result.has_errors()
    assert FurnitureSignpostReal.objects.all().count() == 5


@pytest.mark.parametrize(
    "parent_real_preexists",
    (True, False),
    ids=lambda x: "parent_real_preexists" if x else "parent_real_nonexists",
)
@pytest.mark.parametrize(
    "child_real_preexists",
    (True, False),
    ids=lambda x: "child_real_preexists" if x else "child_real_nonexists",
)
@pytest.mark.django_db
def test__furniture_signpost_plan_export_real_parent_and_child(parent_real_preexists, child_real_preexists):
    plan_parent = get_furniture_signpost_plan()
    plan_child = get_furniture_signpost_plan(parent=plan_parent)

    if parent_real_preexists:
        real_parent = get_furniture_signpost_real(furniture_signpost_plan=plan_parent)
    else:
        real_parent = None

    if child_real_preexists:
        real_child = get_furniture_signpost_real(furniture_signpost_plan=plan_child)
    else:
        real_child = None

    exported_dataset = FurnitureSignpostPlanTemplateResource().export()
    assert len(exported_dataset) == 2

    assert exported_dataset["furniture_signpost_plan__id"] == [
        plan_parent.id,
        plan_child.id,
    ]

    if parent_real_preexists:
        if child_real_preexists:
            expected_ids = [
                real_parent.id,
                real_child.id,
            ]
            expected_parent_ids = [
                None,
                real_parent.id,
            ]
        else:
            expected_ids = [
                real_parent.id,
                None,
            ]
            expected_parent_ids = [
                None,
                real_parent.id,
            ]
    else:
        if child_real_preexists:
            expected_ids = [
                1,
                real_child.id,
            ]
            expected_parent_ids = [
                None,
                1,
            ]
        else:
            expected_ids = [
                1,
                None,
            ]
            expected_parent_ids = [None, 1]

    assert exported_dataset["id"] == expected_ids
    assert exported_dataset["parent__id"] == expected_parent_ids

    # Import
    import_result = FurnitureSignpostRealResource().import_data(exported_dataset, raise_errors=False)
    assert not import_result.has_errors()
    assert FurnitureSignpostReal.objects.all().count() == 2

    imported_parent_real = FurnitureSignpostReal.objects.get(furniture_signpost_plan=plan_parent)
    imported_child_real = FurnitureSignpostReal.objects.get(furniture_signpost_plan=plan_child)
    assert imported_parent_real.parent_id is None
    assert imported_child_real.parent_id == imported_parent_real.id
    assert imported_parent_real.id != UUID(int=1)


@pytest.mark.django_db
def test__furniture_signpost_real__import__responsible_entity_permission__group():
    get_furniture_signpost_real(responsible_entity=get_responsible_entity_project())
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


@pytest.mark.parametrize(
    ("model", "resource", "factory"),
    (
        (FurnitureSignpostReal, FurnitureSignpostRealResource, get_furniture_signpost_real),
        (FurnitureSignpostPlan, FurnitureSignpostPlanResource, get_furniture_signpost_plan),
    ),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db()
def test__furniture_signpost__import__replace_parent_child_ids(model, resource, factory, format):
    """Test that parent and child ids are replaced with the actual objects"""
    parent = factory(location_name_en="A")
    child = factory(location_name_en="B")

    dataset = get_import_dataset(resource, format, delete_columns=["id", "parent__id"])
    dataset = dataset.sort("location_name_en")
    dataset.append_col(["1", None], header="id")
    dataset.append_col([None, "1"], header="parent__id")

    model.objects.all().delete()
    assert model.objects.count() == 0

    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)
    assert not result.has_errors()

    imported_parent = model.objects.get(location_name_en=parent.location_name_en)
    imported_child = model.objects.get(location_name_en=child.location_name_en)
    assert imported_child.parent_id == imported_parent.id
