import pytest

from traffic_control.models import MountPlan, MountReal
from traffic_control.resources import MountPlanResource, MountPlanToRealTemplateResource, MountRealResource
from traffic_control.tests.factories import get_mount_plan, get_mount_real
from traffic_control.tests.import_export.utils import file_formats, get_import_dataset


@pytest.mark.django_db
def test__mount_real__export():
    obj = get_mount_real()
    dataset = MountRealResource().export()

    assert dataset.dict[0]["location"] == str(obj.location)
    assert dataset.dict[0]["owner__name_fi"] == obj.owner.name_fi
    assert dataset.dict[0]["lifecycle"] == obj.lifecycle.name


@pytest.mark.parametrize(
    ("model", "resource", "factory"),
    (
        (MountPlan, MountPlanResource, get_mount_plan),
        (MountReal, MountRealResource, get_mount_real),
    ),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__mount__import(model, resource, factory, format):
    factory()
    dataset = get_import_dataset(resource, format=format, delete_columns=["id"])
    model.objects.all().delete()

    result = resource().import_data(dataset, raise_errors=True)
    assert not result.has_errors()
    assert model.objects.all().count() == 1


@pytest.mark.parametrize("real_preexists", (True, False), ids=lambda x: "real_preexists" if x else "real_nonexists")
@pytest.mark.django_db
def test__mount_plan_export_real_import(real_preexists):
    """Test that a plan object can be exported as its real object (referencing to the plan)"""

    plan_obj = get_mount_plan()
    real_obj = get_mount_real() if real_preexists else None

    exported_dataset = MountPlanToRealTemplateResource().export()
    assert len(exported_dataset) == 1

    real = exported_dataset.dict[0]
    assert real["mount_plan__id"] == plan_obj.id

    if real_preexists:
        assert real["id"] == real_obj.id
    else:
        assert real["id"] is None
