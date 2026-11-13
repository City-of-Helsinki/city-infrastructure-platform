"""Classification of every database table for the sanitized development dump.

Every table of every installed app is either:

- kept: schema and data are dumped as is (``KEEP_APPS``, ``KEEP_TABLES``),
- data excluded: schema is dumped, data is not (``EXCLUDE_DATA_TABLES``),
- scrubbed: schema is dumped, data is exported with personal data replaced (``SCRUB_TABLES``).

Tables that no model owns must be listed in ``NON_MODEL_TABLES``. They are not sanitized: ``django_migrations`` is
dumped as is, and the others belong to PostGIS, which creates them. No dump is made while ``rule_problems()`` reports
anything, and a test fails, so a new table or a new column on a scrubbed table must be classified here.
"""

from collections import Counter
from enum import Enum
from itertools import chain
from typing import Literal

from django.apps import apps
from django.db import connection
from django.db.models import Model


class Keep(Enum):
    """Marks a column of a scrubbed table whose value is copied unchanged."""

    KEEP = "keep"


KEEP = Keep.KEEP
# Rule of one column of a scrubbed table: KEEP, or the SQL expression that replaces the column's value.
ColumnRule = str | Literal[Keep.KEEP]

# Domain and configuration data without personal data.
KEEP_APPS = frozenset(
    {
        "auth",
        "city_furniture",
        "command_tracker",
        "contenttypes",
        "db",  # health_check
        "guardian",
        "map",
        "site_alert",
        "traffic_control",
    }
)

KEEP_TABLES = frozenset(
    {
        "helusers_adgroup",
        "helusers_adgroupmapping",
        "maintenance_mode_maintenancemode",
        "users_user_ad_groups",
        "users_user_groups",
        "users_user_operational_areas",
        "users_user_responsible_entities",
        "users_user_user_permissions",
    }
)

# Credentials, sessions, login attempts, deactivation notices, and admin and audit history.
EXCLUDE_DATA_TABLES = frozenset(
    {
        "auditlog_logentry",
        "authtoken_token",
        "axes_accessattempt",
        "axes_accessfailurelog",
        "axes_accesslog",
        "django_admin_log",
        "django_session",
        "helusers_oidcbackchannellogoutevent",
        "resilient_logger_resilientlogentry",  # log buffer, holds audit log data
        "social_auth_association",
        "social_auth_code",
        "social_auth_nonce",
        "social_auth_partial",
        "social_auth_usersocialauth",
        "user_deactivation_status",
    }
)

# Every column of a scrubbed table, mapped to KEEP or to the SQL expression that replaces its value.
SCRUB_TABLES: dict[str, dict[str, ColumnRule]] = {
    "users_user": {
        "id": KEEP,
        "password": "'!'",  # unusable password
        "last_login": KEEP,
        "is_superuser": KEEP,
        "username": "'user_' || id::text",
        "first_name": "'Dev'",
        "last_name": "left(id::text, 8)",
        "email": "'user_' || id::text || '@example.invalid'",
        "is_staff": KEEP,
        "is_active": KEEP,
        "date_joined": KEEP,
        "uuid": "gen_random_uuid()",  # so that no OIDC login matches the user
        "department_name": "NULL",
        "bypass_operational_area": KEEP,
        "bypass_responsible_entity": KEEP,
        "additional_information": "''",
        "last_api_use": KEEP,
        "reactivated_at": KEEP,
        "receives_admin_notification_emails": KEEP,
    },
}

# Tables that no model owns, as schema.table.
NON_MODEL_TABLES = frozenset(
    {"public.django_migrations", "public.spatial_ref_sys", "topology.layer", "topology.topology"}
)


def models_by_table() -> dict[str, type[Model]]:
    """Return the models that own a database table, keyed by table name.

    Returns:
        dict[str, type[Model]]: Mapping of table name to model class.
    """
    return {
        model._meta.db_table: model
        for model in apps.get_models(include_auto_created=True)
        if model._meta.managed and not model._meta.proxy
    }


def database_tables() -> set[str]:
    """Return every table in the database, as schema.table.

    Returns:
        set[str]: Names of the tables, as schema.table.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT table_schema || '.' || table_name FROM information_schema.tables "
            "WHERE table_type = 'BASE TABLE' AND table_schema NOT IN ('pg_catalog', 'information_schema')"
        )
        return {row[0] for row in cursor.fetchall()}


def rule_problems() -> dict[str, list[str]]:
    """Find the tables and columns that the rules above do not classify correctly.

    Returns:
        dict[str, list[str]]: Description of each problem found, mapped to the offending tables or columns. Empty
            if the rules are complete.
    """
    models = models_by_table()
    model_tables = models.keys()

    # Number of rules that apply to each table. Every model table must have exactly one.
    kept_by_app = {table for table, model in models.items() if model._meta.app_label in KEEP_APPS}
    rule_counts = Counter(chain(kept_by_app, KEEP_TABLES, EXCLUDE_DATA_TABLES, SCRUB_TABLES))

    # A SCRUB_TABLES entry must list exactly the columns of its table.
    mismatched_columns = set()
    for table, rule_columns in SCRUB_TABLES.items():
        if table in models:
            model_columns = {field.column for field in models[table]._meta.concrete_fields}
            mismatched_columns |= {f"{table}.{column}" for column in model_columns ^ rule_columns.keys()}

    problems = {
        "tables without a rule": model_tables - rule_counts.keys(),
        "tables with more than one rule": {table for table, count in rule_counts.items() if count > 1},
        "rule tables without a model": rule_counts.keys() - model_tables,
        "tables without a model, missing from NON_MODEL_TABLES": (
            database_tables() - {f"public.{table}" for table in model_tables} - NON_MODEL_TABLES
        ),
        "columns of scrubbed tables that differ between SCRUB_TABLES and the model": mismatched_columns,
    }
    return {description: sorted(found) for description, found in problems.items() if found}
