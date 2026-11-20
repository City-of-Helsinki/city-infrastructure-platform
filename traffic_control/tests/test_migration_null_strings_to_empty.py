"""Tests for the data migrations that convert NULL to "" in optional string fields.

Postgres DDL is transactional, so each test drops the NOT NULL constraints inside the test
transaction, forces NULLs into real rows and runs the migration's own function against the
historical model state, as ``migrate`` does. Everything is rolled back when the test ends.
"""

from importlib import import_module
from types import ModuleType
from typing import Callable

import pytest
from django.apps import apps
from django.db import connection, migrations, models
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import StateApps

from city_furniture.tests import factories as cf_factories
from traffic_control.serializers.common import accepts_null_as_empty_string
from traffic_control.tests import factories as tc_factories

# (app label, migration before the change, data migration, schema migration)
MIGRATIONS = (
    (
        "traffic_control",
        "0123_importattachmentcleanuprun",
        "0124_null_strings_to_empty",
        "0125_null_strings_not_null",
    ),
    (
        "city_furniture",
        "0029_alter_cityfurnituredevicetype_icon_file",
        "0030_null_strings_to_empty",
        "0031_null_strings_not_null",
    ),
)
ROW_FACTORIES: dict[str, Callable[[], models.Model]] = {
    "plan": tc_factories.PlanFactory,
    "traffic_control_device_type": tc_factories.TrafficControlDeviceTypeFactory,
    "mount_plan": tc_factories.MountPlanFactory,
    "mount_real": tc_factories.MountRealFactory,
    "traffic_sign_plan": tc_factories.TrafficSignPlanFactory,
    "traffic_sign_real": tc_factories.TrafficSignRealFactory,
    "signpost_plan": tc_factories.SignpostPlanFactory,
    "signpost_real": tc_factories.SignpostRealFactory,
    "additional_sign_plan": tc_factories.AdditionalSignPlanFactory,
    "additional_sign_real": tc_factories.AdditionalSignRealFactory,
    "barrier_plan": tc_factories.BarrierPlanFactory,
    "barrier_real": tc_factories.BarrierRealFactory,
    "traffic_control_responsibleentity": tc_factories.ResponsibleEntityFactory,
    "road_marking_plan": tc_factories.RoadMarkingPlanFactory,
    "road_marking_real": tc_factories.RoadMarkingRealFactory,
    "traffic_light_plan": tc_factories.TrafficLightPlanFactory,
    "traffic_light_real": tc_factories.TrafficLightRealFactory,
    "city_furniture_device_type": cf_factories.CityFurnitureDeviceTypeFactory,
    "city_furniture_target": cf_factories.get_city_furniture_target,
    "furniture_signpost_plan": cf_factories.FurnitureSignpostPlanFactory,
    "furniture_signpost_real": cf_factories.FurnitureSignpostRealFactory,
}


def _migration(app_label: str, name: str) -> ModuleType:
    """Import a migration module, whose name cannot be used in an import statement.

    Args:
        app_label (str): App the migration belongs to.
        name (str): Migration name.

    Returns:
        ModuleType: The migration module.
    """
    return import_module(f"{app_label}.migrations.{name}")


def _table_columns() -> dict[str, list[str]]:
    """Collect the converted columns of both apps from the data migrations' field lists.

    Returns:
        dict[str, list[str]]: Column names by table name. Field names equal column names for these fields.
    """
    tables = {}
    for app_label, _before, data_name, _schema_name in MIGRATIONS:
        for model_name, field_names in _migration(app_label, data_name).FIELDS_BY_MODEL.items():
            tables[apps.get_model(app_label, model_name)._meta.db_table] = field_names
    return tables


TABLE_COLUMNS = _table_columns()


@pytest.fixture(scope="module")
def apps_before_the_change() -> StateApps:
    """Build the model state that the data migrations run against: optional string fields still nullable.

    Returns:
        StateApps: Historical app registry at the migrations right before the data migrations.
    """
    loader = MigrationLoader(None, ignore_no_migrations=True)
    return loader.project_state([(app_label, before) for app_label, before, _data, _schema in MIGRATIONS]).apps


@pytest.fixture
def nullable_columns(db: None) -> None:
    """Drop NOT NULL from every converted column for the duration of the test transaction.

    Must run before any rows are created: Postgres refuses ALTER TABLE on a table with
    pending deferred trigger events from inserts in the same transaction.

    Args:
        db (None): pytest-django database fixture.
    """
    with connection.cursor() as cursor:
        for table, columns in TABLE_COLUMNS.items():
            for column in columns:
                cursor.execute(f'ALTER TABLE "{table}" ALTER COLUMN "{column}" DROP NOT NULL')


def _force_values(instance: models.Model, values: dict[str, str | None]) -> None:
    """Write raw values into columns of one row.

    Args:
        instance (models.Model): Saved row to change.
        values (dict[str, str | None]): Raw value per column name.
    """
    with connection.cursor() as cursor:
        assignments = ", ".join(f'"{column}" = %s' for column in values)
        cursor.execute(
            f'UPDATE "{instance._meta.db_table}" SET {assignments} WHERE id = %s', [*values.values(), instance.pk]
        )


def _force_nulls(instance: models.Model) -> None:
    """Set the converted columns of one row to NULL.

    Args:
        instance (models.Model): Saved row whose converted columns are set to NULL.
    """
    _force_values(instance, dict.fromkeys(TABLE_COLUMNS[instance._meta.db_table]))


def _column_values(instance: models.Model) -> dict[str, str | None]:
    """Read the converted columns of a row straight from the database.

    Args:
        instance (models.Model): Row to read.

    Returns:
        dict[str, str | None]: Column name to raw database value.
    """
    columns = TABLE_COLUMNS[instance._meta.db_table]
    with connection.cursor() as cursor:
        quoted = ", ".join(f'"{column}"' for column in columns)
        cursor.execute(f'SELECT {quoted} FROM "{instance._meta.db_table}" WHERE id = %s', [instance.pk])
        return dict(zip(columns, cursor.fetchone(), strict=True))


def _row_version(instance: models.Model) -> tuple[str, str]:
    """Read the physical version of a row, which changes whenever the row is rewritten.

    Args:
        instance (models.Model): Row to look at.

    Returns:
        tuple[str, str]: Postgres' ctid and xmin of the row.
    """
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT ctid::text, xmin::text FROM "{instance._meta.db_table}" WHERE id = %s', [instance.pk])
        return cursor.fetchone()


def _run_data_migrations(state_apps: StateApps) -> None:
    """Run the function of both data migrations the way ``migrate`` does.

    Args:
        state_apps (StateApps): Historical app registry to run them against.
    """
    with connection.schema_editor() as schema_editor:
        for app_label, _before, data_name, _schema_name in MIGRATIONS:
            _migration(app_label, data_name).null_to_empty_string(state_apps, schema_editor)


def test__row_factories__cover_every_converted_table() -> None:
    """The per-table test below would silently skip a table that has no factory."""
    assert ROW_FACTORIES.keys() == TABLE_COLUMNS.keys()


def test__converted_fields__are_optional_non_nullable_string_fields_in_the_models() -> None:
    """Every listed field must be an optional string field that the models now declare null=False."""
    for app_label, _before, data_name, _schema_name in MIGRATIONS:
        for model_name, field_names in _migration(app_label, data_name).FIELDS_BY_MODEL.items():
            model = apps.get_model(app_label, model_name)
            for field_name in field_names:
                assert accepts_null_as_empty_string(model._meta.get_field(field_name)), f"{model_name}.{field_name}"


@pytest.mark.parametrize("app_label, before, data_name, schema_name", MIGRATIONS)
def test__schema_migration__alters_exactly_the_fields_the_data_migration_converts(
    app_label: str, before: str, data_name: str, schema_name: str
) -> None:
    """A field made NOT NULL without its NULLs being converted first would only fail at deploy time."""
    data_migration = _migration(app_label, data_name)
    schema_migration = _migration(app_label, schema_name).Migration
    converted = {
        (model_name.lower(), field_name)
        for model_name, field_names in data_migration.FIELDS_BY_MODEL.items()
        for field_name in field_names
    }

    assert all(isinstance(operation, migrations.AlterField) for operation in schema_migration.operations)
    assert {(operation.model_name, operation.name) for operation in schema_migration.operations} == converted
    assert all(operation.field.null is False for operation in schema_migration.operations)
    assert schema_migration.dependencies == [(app_label, data_name)]
    assert data_migration.Migration.dependencies == [(app_label, before)]


@pytest.mark.usefixtures("nullable_columns")
@pytest.mark.parametrize("table", TABLE_COLUMNS.keys())
def test__data_migration__converts_nulls_in_every_converted_table(
    table: str, apps_before_the_change: StateApps
) -> None:
    """Guards the model and field names in the lists against typos, one real row per table."""
    row = ROW_FACTORIES[table]()
    assert row._meta.db_table == table
    _force_nulls(row)

    _run_data_migrations(apps_before_the_change)

    assert set(_column_values(row).values()) == {""}
    with connection.cursor() as cursor:
        for column in TABLE_COLUMNS[table]:
            cursor.execute(f'SELECT count(*) FROM "{table}" WHERE "{column}" IS NULL')
            assert cursor.fetchone()[0] == 0, f"{table}.{column}"


@pytest.mark.usefixtures("nullable_columns")
def test__data_migration__changes_only_nulls_and_only_rows_that_have_one(apps_before_the_change: StateApps) -> None:
    """Existing values survive, also odd ones, and rows without a NULL are not rewritten at all."""
    sign_with_nulls = tc_factories.TrafficSignRealFactory(is_active=False)
    _force_nulls(sign_with_nulls)
    sign_with_values = tc_factories.TrafficSignRealFactory(txt="Keep me", road_name=" ", rfid="")
    values_before = _column_values(sign_with_values)
    row_version_before = _row_version(sign_with_values)
    sign_with_one_null = tc_factories.TrafficSignRealFactory(txt="None", road_name="ääkköset 🚦")
    _force_values(sign_with_one_null, {"rfid": None})

    _run_data_migrations(apps_before_the_change)

    assert set(_column_values(sign_with_nulls).values()) == {""}
    assert _column_values(sign_with_values) == values_before
    assert _row_version(sign_with_values) == row_version_before
    one_null_values = _column_values(sign_with_one_null)
    assert (one_null_values["rfid"], one_null_values["txt"], one_null_values["road_name"]) == (
        "",
        "None",
        "ääkköset 🚦",
    )
