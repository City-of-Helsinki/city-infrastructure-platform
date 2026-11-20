from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps
from django.db.models import Q, Value
from django.db.models.functions import Coalesce

_FURNITURE_SIGNPOST_FIELDS = [
    "location_name_fi",
    "location_name_sw",
    "location_name_en",
    "location_additional_info",
    "size",
    "pictogram",
    "text_content_fi",
    "text_content_sw",
    "text_content_en",
    "content_responsible_entity",
    "additional_material_url",
]
# Optional string fields that the next migration makes NOT NULL, by model.
FIELDS_BY_MODEL = {
    "CityFurnitureDeviceType": ["description_fi", "description_sw", "description_en"],
    "CityFurnitureTarget": ["name_sw", "name_en", "description"],
    "FurnitureSignpostPlan": _FURNITURE_SIGNPOST_FIELDS,
    "FurnitureSignpostReal": _FURNITURE_SIGNPOST_FIELDS,
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
        model = apps.get_model("city_furniture", model_name)
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
        ("city_furniture", "0029_alter_cityfurnituredevicetype_icon_file"),
    ]

    operations = [
        # Backwards is a no-op: the NULLs that were there cannot be told apart from "" afterwards.
        migrations.RunPython(null_to_empty_string, reverse_code=migrations.RunPython.noop),
    ]
