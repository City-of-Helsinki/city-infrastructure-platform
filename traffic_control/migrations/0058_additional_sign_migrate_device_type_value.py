from django.db import migrations
from django.db import transaction

# Additional sign reals' legacy codes that are in test and production environments.
# TrafficControlDeviceType has legacy code defined, but not all so that is why
# this dict is defined here.
# Some legacy codes don't have corresponding device type, or are likely not correct.
# Those are defined here to get value None (device type is not defined).
legacy_code_to_device_type_code = {
    "812": "H2.1",
    "814": "H3",
    "815": "H4",
    "822": "H7",
    "823": "H8",
    "824": "H9.1",
    "825": "H9.2",
    "826": "H10",
    "827": None,
    "828": "H11",
    "831": "H12.1",
    "832": "H12.2",
    "833": "H12.3",
    "833.1": "H12.3",
    "834": "H12.4",
    "835": "H12.5",
    "836": "H12.7",
    "841": "H12.8",
    "845": "H13.2",
    "848": "H14",
    "851": "H17.1",
    "852": "H17.2",
    "854": "H17.3",
    "855": "H20",
    "856": "H19.1",
    "861": "H22.1",
    "863": "H23.1",
    "871": None,
    "872": "H23.1",
    "811-L": "H1_2",
    "811-R": "H1",
    "812-L": "H2.11",
    "812-R": "H2.1",
    "826-L": "H10_2",
    "826-R": "H10",
    "855a": "H20",
    "855b": "H20S",
    "856b": "H19.2",
    "871_2": None,
    "871_4": None,
    "871blue": None,
}


def legacy_code_to_device_code(apps, schema_editor):
    AdditionalSignReal = apps.get_model("traffic_control", "AdditionalSignReal")
    TrafficControlDeviceType = apps.get_model("traffic_control", "TrafficControlDeviceType")
    db_alias = schema_editor.connection.alias

    device_types = TrafficControlDeviceType.objects.all()

    for legacy_code in legacy_code_to_device_type_code:
        device_type_code = legacy_code_to_device_type_code[legacy_code]
        device_type = device_types.filter(code=device_type_code).first()

        if device_type is not None:
            # Select additional signs that have legacy code but no device type defined
            additional_signs = (
                AdditionalSignReal.objects.using(db_alias)
                .select_for_update()
                .filter(
                    legacy_code=legacy_code,
                    device_type=None,
                )
            )
            with transaction.atomic():
                additional_signs.update(device_type=device_type)


def reverse(apps, schema_editor):
    # Allow reversing migration for dev purposes, but don't reverse the actual change.
    return


class Migration(migrations.Migration):

    dependencies = [
        ("traffic_control", "0057_device_type_validate_content_schema"),
    ]

    operations = [
        migrations.RunPython(legacy_code_to_device_code, reverse),
    ]
