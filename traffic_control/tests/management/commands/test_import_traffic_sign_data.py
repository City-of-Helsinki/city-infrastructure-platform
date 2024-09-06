import datetime
import os
from decimal import Decimal

import pytest
from django.core.management import call_command

from traffic_control.analyze_utils.traffic_sign_data import get_default_installation_status, TrafficSignImporter
from traffic_control.enums import Condition
from traffic_control.models import (
    AdditionalSignReal,
    MountReal,
    MountType,
    SignpostReal,
    TrafficControlDeviceType,
    TrafficSignReal,
)
from traffic_control.models.additional_sign import Color
from traffic_control.models.mount import LocationSpecifier as MountLocationSpecifier
from traffic_control.models.traffic_sign import LocationSpecifier as SignLocationSpecifier

BASE_PATH = os.path.dirname(__file__)
TEST_FILES_DIR = os.path.join(BASE_PATH, "../../test_datas/traffic_sign_import")


def _create_db_entries():
    device_type_codes = ["C39", "H24S", "4171"]
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    for code in device_type_codes:
        TrafficControlDeviceType.objects.get_or_create(code=code)


@pytest.mark.django_db
def test__import_traffic_scan_data():
    _create_db_entries()
    importer = TrafficSignImporter(None, None, None)
    call_command(
        "import_traffic_sign_data",
        sign_file=os.path.join(TEST_FILES_DIR, "basic_panels.csv"),
        mount_file=os.path.join(TEST_FILES_DIR, "basic_mounts.csv"),
    )

    _assert_mount_data(importer)
    _assert_traffic_sign_data(importer)
    _assert_additional_sign_data(importer)
    _assert_signpost_data()


def _assert_mount_data(importer):
    assert 1 == MountReal.objects.count()
    mount = MountReal.objects.first()

    assert mount.mount_type == MountType.objects.get(code="POLE")
    assert mount.source_id == "mount_pylväs1"
    assert mount.source_name == importer.SOURCE_NAME
    assert mount.location.x == 25497188.8384
    assert mount.location.y == 6673461.8389
    assert mount.location.z == 5.27
    assert mount.owner == importer.default_owner
    assert mount.installation_status == get_default_installation_status()
    assert mount.scanned_at == datetime.datetime(2023, 8, 15, 12, 28, 0, tzinfo=datetime.timezone.utc)
    assert mount.location_specifier == MountLocationSpecifier.OUTSIDE


def _assert_traffic_sign_data(importer):
    assert 1 == TrafficSignReal.objects.count()
    mount = MountReal.objects.first()
    sign = TrafficSignReal.objects.first()

    assert sign.owner == importer.default_owner
    assert sign.device_type.code == "C39"
    assert sign.scanned_at == datetime.datetime(2023, 8, 15, 12, 28, 0, tzinfo=datetime.timezone.utc)
    assert sign.value == Decimal("30")
    assert sign.source_id == "basic_sign"
    assert sign.source_name == importer.SOURCE_NAME
    assert sign.location.x == 25497188.8384
    assert sign.location.y == 6673461.8389
    assert sign.location.z == 7.64
    assert sign.direction == 91
    assert sign.height == 236
    assert sign.condition == Condition.BAD
    assert sign.mount_real == mount
    assert sign.mount_type == mount.mount_type
    assert sign.txt == "TestiTeksti"
    assert sign.installation_status == get_default_installation_status()
    assert sign.location_specifier == SignLocationSpecifier.OUTSIDE


def _assert_additional_sign_data(importer):
    assert 1 == AdditionalSignReal.objects.count()
    mount = MountReal.objects.first()
    sign = TrafficSignReal.objects.first()
    additional = AdditionalSignReal.objects.first()

    assert additional.owner == importer.default_owner
    assert additional.device_type.code == "H24S"
    assert additional.scanned_at == datetime.datetime(2023, 8, 14, 10, 14, 36, tzinfo=datetime.timezone.utc)
    assert additional.source_id == "basic_additional_sign"
    assert additional.source_name == importer.SOURCE_NAME
    assert additional.location.x == 25498102.0919
    assert additional.location.y == 6672508.0929
    assert additional.location.z == 4.31
    assert additional.direction == 297
    assert additional.height == 162
    assert additional.condition == Condition.GOOD
    assert additional.mount_real == mount
    assert additional.mount_type == mount.mount_type
    assert additional.parent == sign
    assert additional.installation_status == get_default_installation_status()
    assert additional.location_specifier == SignLocationSpecifier.ABOVE
    assert additional.color == Color.BLUE
    assert additional.additional_information == "text:Yksityisalue; numbercode:"
    assert additional.missing_content is True


def _assert_signpost_data():
    """All signpost imports are skipped for now"""
    assert 0 == SignpostReal.objects.count()


@pytest.mark.parametrize(
    ("code", "csv_value", "expected_db_value"),
    (
        ("C39", "1", SignLocationSpecifier.RIGHT),
        ("C39", "2", SignLocationSpecifier.LEFT),
        ("C39", "3", SignLocationSpecifier.ABOVE),
        ("C39", "4", SignLocationSpecifier.MIDDLE),
        ("C39", "5", SignLocationSpecifier.VERTICAL),
        ("C39", "6", SignLocationSpecifier.OUTSIDE),
        ("C39", "", None),
        ("4171", "", SignLocationSpecifier.MIDDLE),
        ("4171", "1", SignLocationSpecifier.RIGHT),
    ),
)
@pytest.mark.django_db
def test__traffic_sign_import_location_specifier(code, csv_value, expected_db_value):
    _create_db_entries()
    mount_data = _get_mount_dict({})
    sign_data = _get_sign_dict({"Sijaintitarkenne": csv_value, "merkkikoodi": code})
    importer = TrafficSignImporter(mount_data, sign_data, {})
    importer.import_data()

    assert TrafficSignReal.objects.count() == 1
    sign = TrafficSignReal.objects.first()
    assert sign.location_specifier == expected_db_value


@pytest.mark.parametrize(
    ("csv_value", "expected_db_value"),
    (
        ("unreadable", None),
        ("300", 300),
        ("1", 1),
        ("25 m", 25),
        ("30 foo bar", 30),
    ),
)
@pytest.mark.django_db
def test__traffic_sign_import_value(csv_value, expected_db_value):
    _create_db_entries()
    mount_data = _get_mount_dict({})
    sign_data = _get_sign_dict({"numerokoodi": csv_value})
    importer = TrafficSignImporter(mount_data, sign_data, {})
    importer.import_data()

    assert TrafficSignReal.objects.count() == 1
    sign = TrafficSignReal.objects.first()
    assert sign.value == expected_db_value


@pytest.mark.parametrize(("csv_height", "expected_db_height"), (("1.52", 152),))
@pytest.mark.django_db
def test__traffic_sign_import_height(csv_height, expected_db_height):
    _create_db_entries()
    mount_data = _get_mount_dict({})
    sign_data = _get_sign_dict({"korkeus": csv_height})
    importer = TrafficSignImporter(mount_data, sign_data, {})
    importer.import_data()

    assert TrafficSignReal.objects.count() == 1
    sign = TrafficSignReal.objects.first()
    assert sign.height == expected_db_height


@pytest.mark.parametrize(
    ("csv_color", "expected_db_color"),
    (
        ("1", Color.BLUE),
        ("2", Color.YELLOW),
        ("", None),
        ("25", None),
        ("notanumber", None),
    ),
)
@pytest.mark.django_db
def test__additional_sign_import_color(csv_color, expected_db_color):
    _create_db_entries()
    mount_data = _get_mount_dict({})
    sign_data = _get_sign_dict({"taustaväri": csv_color, "merkkikoodi": "H24S", "lisäkilven_päämerkin_id": "dummyid"})
    importer = TrafficSignImporter(mount_data, {}, sign_data)
    importer.import_data()

    assert AdditionalSignReal.objects.count() == 1
    add_sign = AdditionalSignReal.objects.first()
    assert add_sign.color == expected_db_color


@pytest.mark.parametrize(
    ("csv_text", "csv_numbercode", "expected_db_additional_information"),
    (
        ("", "", "text:; numbercode:"),
        (" ", "     ", "text:; numbercode:"),
        ("  TestText  ", "     ", "text:TestText; numbercode:"),
        ("TestText", " TestNumberCOde ", "text:TestText; numbercode:TestNumberCOde"),
    ),
)
@pytest.mark.django_db
def test__additional_sign_import_additional_information(csv_text, csv_numbercode, expected_db_additional_information):
    _create_db_entries()
    mount_data = _get_mount_dict({})
    sign_data = _get_sign_dict(
        {"teksti": csv_text, "numerokoodi": csv_numbercode, "merkkikoodi": "H24S", "lisäkilven_päämerkin_id": "dummyid"}
    )
    importer = TrafficSignImporter(mount_data, {}, sign_data)
    importer.import_data()

    assert AdditionalSignReal.objects.count() == 1
    add_sign = AdditionalSignReal.objects.first()
    assert add_sign.additional_information == expected_db_additional_information


def _get_sign_dict(update_params):
    base_dict = {
        "fid": 1,
        "OBJECTID": "3",
        "id": "sign",
        "x": 25497188.8384,
        "y": 6673461.8389,
        "z": 5.27,
        "stdx": 0.014,
        "stdy": 0.009,
        "stdz": 0.022,
        "kiinnityskohta_id": "",
        "merkkikoodi": "C39",
        "teksti": "TestiTeksti",
        "teksti_suomeksi": "TestiTeksti",
        "teksti_ruotsiksi": "Samma på svenska",
        "kiinnitys": "Pylväs",
        "numerokoodi": "30 m",
        "merkin_ehto": "2",
        "taustaväri": "1",
        "atsimuutti": "90",
        "lisäkilven_päämerkin_id": "",
        "tallennusajankohta": "2023/08/15 12:28:00+00",
        "korkeus": 1.50,
        "ssurl": "https://dummy",
        "Sijaintitarkenne": "6",
        "Muokattu_info": "",
    }
    base_dict.update(update_params)
    return {"sign": base_dict}


def _get_mount_dict(update_params):
    base_dict = {
        "fid": 1,
        "OBJECTID": "3",
        "id": "mount_pylväs1",
        "x": 25497188.8384,
        "y": 6673461.8389,
        "z": 5.27,
        "stdx": 0.014,
        "stdy": 0.009,
        "stdz": 0.022,
        "tyyppi": "Pylväs",
        "tallennusajankohta": "2023/08/15 12:28:00+00",
        "ssurl": "https://dummy",
        "Sijaintitarkenne": "6",
    }
    base_dict.update(update_params)
    return {"mount_pylväst1": base_dict}
