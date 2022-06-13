import pytest

from traffic_control.models import AdditionalSignReal
from traffic_control.resources.additional_sign import AdditionalSignRealResource
from traffic_control.tests.factories import get_additional_sign_real


@pytest.mark.django_db
def test__additional_sign_real__export():
    obj = get_additional_sign_real()
    dataset = AdditionalSignRealResource().export()

    assert dataset.dict[0]["location"] == str(obj.location)
    assert dataset.dict[0]["owner__name_fi"] == obj.owner.name_fi
    assert dataset.dict[0]["lifecycle"] == obj.lifecycle.name


@pytest.mark.django_db
def test__additional_sign_real__import():
    get_additional_sign_real()
    dataset = AdditionalSignRealResource().export()
    AdditionalSignReal.objects.all().delete()

    # Remove ID from data to create new objects
    obj_data = dataset.dict[0]
    obj_data.pop("id")
    dataset.dict = [obj_data]

    result = AdditionalSignRealResource().import_data(dataset, raise_errors=True)
    assert not result.has_errors()
    assert AdditionalSignReal.objects.all().count() == 1
