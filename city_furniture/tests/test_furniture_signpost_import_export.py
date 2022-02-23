import pytest

from city_furniture.models import FurnitureSignpostReal
from city_furniture.resources.furniture_signpost import FurnitureSignpostRealResource
from city_furniture.tests.factories import get_furniture_signpost_real


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
