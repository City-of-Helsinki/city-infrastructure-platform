import pytest

from traffic_control.models import MountReal
from traffic_control.resources.mount import MountPlanToRealTemplateResource, MountRealResource
from traffic_control.tests.factories import get_mount_plan, get_mount_real


@pytest.mark.django_db
def test__mount_real__export():
    obj = get_mount_real()
    dataset = MountRealResource().export()

    assert dataset.dict[0]["location"] == str(obj.location)
    assert dataset.dict[0]["owner__name_fi"] == obj.owner.name_fi
    assert dataset.dict[0]["lifecycle"] == obj.lifecycle.name


@pytest.mark.django_db
def test__mount_real__import():
    get_mount_real()
    dataset = MountRealResource().export()
    MountReal.objects.all().delete()

    # Remove ID from data to create new objects
    obj_data = dataset.dict[0]
    obj_data.pop("id")
    dataset.dict = [obj_data]

    result = MountRealResource().import_data(dataset, raise_errors=True)
    assert not result.has_errors()
    assert MountReal.objects.all().count() == 1


@pytest.mark.django_db
def test__mount_plan_export_real_import():
    """Test that a plan object can be exported as its real object (referencing to the plan)"""

    plan_obj = get_mount_plan()

    exported_dataset = MountPlanToRealTemplateResource().export()
    assert len(exported_dataset) == 1

    real = exported_dataset.dict[0]
    assert real["id"] is None
    assert real["mount_plan__id"] == plan_obj.id
