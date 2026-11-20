from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps
from django.db.models import Q, Value
from django.db.models.functions import Coalesce

# Optional string fields that the next migration makes NOT NULL, by model.
FIELDS_BY_MODEL = {
    "Plan": ["decision_url"],
    "TrafficControlDeviceType": ["description", "legacy_code", "legacy_description"],
    "MountPlan": ["material", "txt", "electric_accountable", "road_name"],
    "MountReal": ["material", "txt", "electric_accountable", "road_name", "attachment_url"],
    "TrafficSignPlan": ["road_name", "txt"],
    "TrafficSignReal": [
        "road_name",
        "txt",
        "legacy_code",
        "installation_id",
        "installation_details",
        "permit_decision_id",
        "manufacturer",
        "rfid",
        "operation",
        "attachment_url",
    ],
    "SignpostPlan": ["road_name", "txt", "attachment_class", "target_id", "target_txt", "electric_maintainer"],
    "SignpostReal": [
        "road_name",
        "txt",
        "attachment_class",
        "target_id",
        "target_txt",
        "electric_maintainer",
        "material",
        "organization",
        "manufacturer",
        "attachment_url",
    ],
    "AdditionalSignPlan": ["road_name"],
    "AdditionalSignReal": [
        "road_name",
        "installation_id",
        "installation_details",
        "installed_by",
        "manufacturer",
        "rfid",
        "legacy_code",
        "permit_decision_id",
        "operation",
        "attachment_url",
    ],
    "BarrierPlan": ["material", "txt"],
    "BarrierReal": ["material", "txt"],
    "ResponsibleEntity": ["external_id"],
    "RoadMarkingPlan": [
        "road_name",
        "value",
        "material",
        "type_specifier",
        "symbol",
        "size",
        "additional_info",
        "amount",
    ],
    "RoadMarkingReal": [
        "road_name",
        "value",
        "material",
        "type_specifier",
        "symbol",
        "size",
        "additional_info",
        "amount",
        "missing_traffic_sign_real_txt",
    ],
    "TrafficLightPlan": ["road_name", "txt"],
    "TrafficLightReal": ["road_name", "txt"],
}


def null_to_empty_string(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Replace NULL with "" in the optional string fields that the next migration makes NOT NULL.

    Django does not convert existing NULLs when a field goes from null=True to null=False without a
    default, so it has to be done first. One UPDATE per model, touching only rows that have a NULL
    in one of the fields. ``update()`` leaves updated_at and the audit log alone.

    Args:
        apps (StateApps): Historical app registry.
        schema_editor (BaseDatabaseSchemaEditor): Schema editor of the running migration.
    """
    for model_name, field_names in FIELDS_BY_MODEL.items():
        model = apps.get_model("traffic_control", model_name)
        has_null = Q()
        for field_name in field_names:
            has_null |= Q(**{f"{field_name}__isnull": True})
        model._base_manager.using(schema_editor.connection.alias).filter(has_null).update(
            **{
                field_name: Coalesce(field_name, Value(""), output_field=model._meta.get_field(field_name))
                for field_name in field_names
            }
        )


class Migration(migrations.Migration):
    dependencies = [
        ("traffic_control", "0123_importattachmentcleanuprun"),
    ]

    operations = [
        # Backwards is a no-op: the NULLs that were there cannot be told apart from "" afterwards.
        migrations.RunPython(null_to_empty_string, reverse_code=migrations.RunPython.noop),
    ]
