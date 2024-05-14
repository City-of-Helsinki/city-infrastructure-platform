from uuid import UUID

import pytest

from traffic_control.models import SignpostPlan, SignpostReal
from traffic_control.resources.signpost import (
    SignpostPlanResource,
    SignpostPlanToRealTemplateResource,
    SignpostRealResource,
)
from traffic_control.tests.factories import get_mount_plan, get_mount_real, get_signpost_plan, get_signpost_real
from traffic_control.tests.test_base_api import test_point_2
from traffic_control.tests.test_import_export.utils import file_formats, get_import_dataset


@pytest.mark.django_db
def test__signpost_real__export():
    obj = get_signpost_real()
    dataset = SignpostRealResource().export()

    assert dataset.dict[0]["location"] == str(obj.location)
    assert dataset.dict[0]["owner__name_fi"] == obj.owner.name_fi
    assert dataset.dict[0]["lifecycle"] == obj.lifecycle.name


@pytest.mark.django_db
def test__signpost_real__import():
    get_signpost_real()
    dataset = SignpostRealResource().export()
    SignpostReal.objects.all().delete()

    # Remove ID from data to create new objects
    obj_data = dataset.dict[0]
    obj_data.pop("id")
    dataset.dict = [obj_data]

    result = SignpostRealResource().import_data(dataset, raise_errors=True)
    assert not result.has_errors()
    assert SignpostReal.objects.all().count() == 1


@pytest.mark.parametrize("has_mount_plan", (True, False), ids=lambda x: "mount_plan" if x else "no_mount_plan")
@pytest.mark.parametrize("has_mount_real", (True, False), ids=lambda x: "mount_real" if x else "no_mount_real")
@pytest.mark.parametrize("has_parent_plan", (True, False), ids=lambda x: "parent_plan" if x else "no_parent_plan")
@pytest.mark.parametrize("has_parent_real", (True, False), ids=lambda x: "parent_real" if x else "no_parent_real")
@pytest.mark.parametrize("real_preexists", (True, False), ids=lambda x: "real_preexists" if x else "real_nonexists")
@pytest.mark.django_db
def test__signpost_plan_export_real_import(
    has_mount_plan,
    has_mount_real,
    has_parent_plan,
    has_parent_real,
    real_preexists,
):
    """Test that a plan object can be exported as its real object (referencing to the plan)"""

    mount_plan = get_mount_plan() if has_mount_plan else None
    mount_real = get_mount_real() if has_mount_real else None
    parent_plan = get_signpost_plan() if has_parent_plan else None
    parent_real = get_signpost_real() if has_parent_real else None

    plan_obj = get_signpost_plan(location=test_point_2, mount_plan=mount_plan, parent=parent_plan)
    real_obj = get_signpost_real(location=test_point_2, signpost_plan=plan_obj) if real_preexists else None

    exported_dataset = SignpostPlanToRealTemplateResource().export(queryset=SignpostPlan.objects.filter(id=plan_obj.id))
    assert len(exported_dataset) == 1

    real = exported_dataset.dict[0]
    assert real["signpost_plan__id"] == plan_obj.id

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
def test__signpost_plan_export_real_replacement_importable():
    """
    Test that a plan objects can be exported to real objects with parent-child id replacements
    and the result is importable.
    """

    get_signpost_plan(location="POINT Z(1 0 0)")
    plan_b = get_signpost_plan(location="POINT Z(2 0 0)")
    get_signpost_plan(location="POINT Z(3 0 0)", parent=plan_b)
    plan_d = get_signpost_plan(location="POINT Z(4 0 0)", parent=plan_b)
    get_signpost_plan(location="POINT Z(5 0 0)", parent=plan_d)

    exported_dataset = SignpostPlanToRealTemplateResource().export()
    assert len(exported_dataset) == 5

    import_result = SignpostRealResource().import_data(exported_dataset, raise_errors=False)
    assert not import_result.has_errors()
    assert SignpostReal.objects.all().count() == 5


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
def test__signpost_plan_export_real_parent_and_child(parent_real_preexists, child_real_preexists):
    plan_parent = get_signpost_plan()
    plan_child = get_signpost_plan(parent=plan_parent)

    if parent_real_preexists:
        real_parent = get_signpost_real(signpost_plan=plan_parent)
    else:
        real_parent = None

    if child_real_preexists:
        real_child = get_signpost_real(signpost_plan=plan_child)
    else:
        real_child = None

    exported_dataset = SignpostPlanToRealTemplateResource().export()
    assert len(exported_dataset) == 2

    assert exported_dataset["signpost_plan__id"] == [
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
    import_result = SignpostRealResource().import_data(exported_dataset, raise_errors=False)
    assert not import_result.has_errors()
    assert SignpostReal.objects.all().count() == 2

    imported_parent_real = SignpostReal.objects.get(signpost_plan=plan_parent)
    imported_child_real = SignpostReal.objects.get(signpost_plan=plan_child)
    assert imported_parent_real.parent_id is None
    assert imported_child_real.parent_id == imported_parent_real.id
    assert imported_parent_real.id != UUID(int=1)


@pytest.mark.parametrize(
    ("model", "resource", "factory"),
    (
        (SignpostReal, SignpostRealResource, get_signpost_real),
        (SignpostPlan, SignpostPlanResource, get_signpost_plan),
    ),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db()
def test__signpost__import__replace_parent_child_ids(model, resource, factory, format):
    """Test that parent and child ids are replaced with the actual objects"""
    parent = factory(txt="A")
    child = factory(txt="B")

    dataset = get_import_dataset(resource, format, delete_columns=["id", "parent__id"])
    dataset = dataset.sort("txt")
    dataset.append_col(["1", None], header="id")
    dataset.append_col([None, "1"], header="parent__id")

    model.objects.all().delete()
    assert model.objects.count() == 0

    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)
    assert not result.has_errors()

    imported_parent = model.objects.get(txt=parent.txt)
    imported_child = model.objects.get(txt=child.txt)
    assert imported_child.parent_id == imported_parent.id
