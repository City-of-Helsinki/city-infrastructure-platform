import pytest
from django.apps import apps

# Guarantee that objects that are supposed to be created by migrations exist
# To find out if anything is missing run:
# git grep -Irn "get_or_create" | grep migrations


@pytest.fixture(autouse=True)
def guarantee_initial_colors_from_city_furniture_migrations(db):
    """
    Guarantee the existence of the colors from
    city_furniture/migrations/0002_initial_colors.py
    """
    CityFurnitureColor = apps.get_model("city_furniture", "CityFurnitureColor")

    initial_colors = (
        # refs. https://brand.hel.fi/en/colours/
        ("Coat of Arms", "#0072C6"),
        ("Gold", "#C2A251"),
        ("Silver", "#DEDFE1"),
        ("Brick", "#BD2719"),
        ("Bus", "#0000BF"),
        ("Copper", "#00D7A7"),
        ("Engel", "#FFE977"),
        ("Fog", "#9FC9EB"),
        ("Metro", "#FD4F00"),
        ("Summer", "#FFC61E"),
        ("Suomenlinna", "#F5A3C7"),
        ("Tram", "#008741"),
        # refs. https://kaupunkitilaohje.hel.fi/kortti/rantareittien-opastus/
        ("Kantakaupunki", "#C2A251"),
        ("Seurasaarenselkä", "#A6E6FF"),
        ("Lauttasaari", "#FF8CFF"),
        ("Kruunuvuorenselkä", "#FFFFFF"),
        ("Vanhankaupunginlahti", "#59FF66"),
        ("Laajasalo", "#F2FF59"),
        ("Itäinen Helsinki", "#FF9980"),
    )

    for name, rgb in initial_colors:
        CityFurnitureColor.objects.get_or_create(name=name, defaults=dict(rgb=rgb))


@pytest.fixture(autouse=True)
def guarantee_device_type_from_city_furniture_migrations(db):
    """
    Guarantee the existence of city furniture device types from
    city_furniture/migrations/0026_set_device_type_non_nullable.py
    """
    CityFurnitureDeviceType = apps.get_model("city_furniture", "CityFurnitureDeviceType")

    # Get or create the DummyDT device type
    # Using integer values directly since enums may not be available in migrations
    dummy_dt, created = CityFurnitureDeviceType.objects.get_or_create(
        code="DummyDT",
        defaults={
            "description_fi": "Paikanpitäjä laitteille, joilla ei ole device_type asetettu",
            "description_en": "Placeholder for devices that have None set to device_type",
            "class_type": 1030,  # CityFurnitureClassType.OTHERS
            "function_type": 1090,  # CityFurnitureFunctionType.FREE_STANDING_SIGN
            "target_model": None,
        },
    )


@pytest.fixture(autouse=True)
def guarantee_device_type_from_traffic_control_migrations(db):
    """
    Guarantee the existence of traffic control device types from
    traffic_control/migrations/0105_set_device_type_non_nullable.py
    """
    TrafficControlDeviceType = apps.get_model("traffic_control", "TrafficControlDeviceType")

    # Get or create the DummyDT device type
    dummy_dt, created = TrafficControlDeviceType.objects.get_or_create(
        code="DummyDT",
        defaults={
            "description": "Placeholder for devices that have None set to device_type",
            "target_model": None,
        },
    )


@pytest.fixture(autouse=True)
def guarantee_owners_from_traffic_control_migrations(db):
    """
    Guarantee the existence of traffic control owners from
    traffic_control/migrations/0022_initial_owners.py

    Note: The owner creation process has more creation/setup steps during the migration,
          but those steps don't seem to be relevant to the current tests.
    """

    Owner = apps.get_model("traffic_control", "Owner")
    initial_owners = (
        ("City of Helsinki", "Helsingin kaupunki"),
        ("State", "Valtio"),
        ("Private", "Yksityinen"),
        ("Unknown", "Ei tiedossa"),
    )

    for name_en, name_fi in initial_owners:
        Owner.objects.get_or_create(name_en=name_en, name_fi=name_fi)
