import random

import factory
from factory.django import DjangoModelFactory

from traffic_control.enums import Condition, InstallationStatus, Lifecycle, Reflection, Size, Surface
from traffic_control.models import TrafficSignReal


def get_random_point():
    x = round(random.uniform(25491148.0, 25513330.0), 2)
    y = round(random.uniform(6670750.0, 6685725.0), 2)
    z = round(random.uniform(5.0, 100.0), 2)
    return "SRID=3879;POINT Z (" + " ".join([str(coord) for coord in [x, y, z]]) + ")"


def get_enum_choices(enum):
    return [choice.value for choice in enum]


class TrafficSignRealFactory(DjangoModelFactory):
    source_name = "Faker"
    location = factory.LazyFunction(get_random_point)
    road_name = factory.Faker("street_name", locale="fi_FI")
    height = factory.Faker("pyfloat", positive=True, min_value=100.0, max_value=300.0)
    direction = factory.Faker("pyint", min_value=0, max_value=359)
    lifecycle = factory.Faker("random_element", elements=get_enum_choices(Lifecycle))
    installation_date = factory.Faker("date_between", start_date="-5y", end_date="today")
    installation_status = factory.Faker("random_element", elements=get_enum_choices(InstallationStatus))
    condition = factory.Faker("random_element", elements=get_enum_choices(Condition))
    size = factory.Faker("random_element", elements=get_enum_choices(Size))
    reflection_class = factory.Faker("random_element", elements=get_enum_choices(Reflection))
    surface_class = factory.Faker("random_element", elements=get_enum_choices(Surface))

    class Meta:
        model = TrafficSignReal
