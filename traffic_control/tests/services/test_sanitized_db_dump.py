import io
import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.db import connection, models
from rest_framework.authtoken.models import Token

from traffic_control.services.sanitized_db_dump import SanitizedDumpError, write_sanitized_dump
from traffic_control.services.sanitized_db_dump_rules import (
    KEEP,
    KEEP_APPS,
    KEEP_TABLES,
    models_by_table,
    rule_problems,
    SCRUB_TABLES,
)
from traffic_control.tests.factories import TrafficSignRealFactory, UserFactory

# Occurs nowhere in the schema, so any occurrence in a dump is leaked data.
PERSONAL_DATA_MARKER = "qzxsecret"
PERSONAL_EMAIL = f"{PERSONAL_DATA_MARKER}@example.com"


@pytest.mark.django_db
def test_rules_classify_every_table_and_column_of_scrubbed_tables() -> None:
    assert rule_problems() == {}


def test_kept_columns_have_no_email_or_ip_fields() -> None:
    # Kept tables and the kept columns of scrubbed tables are dumped as is.
    offending_columns = []
    for table, model in models_by_table().items():
        table_kept = table in KEEP_TABLES or model._meta.app_label in KEEP_APPS
        columns = SCRUB_TABLES.get(table)
        if not table_kept and columns is None:
            continue
        offending_columns += [
            f"{table}.{field.column}"
            for field in model._meta.concrete_fields
            if isinstance(field, (models.EmailField, models.GenericIPAddressField))
            and (table_kept or columns[field.column] is KEEP)
        ]
    assert offending_columns == []


def _psql(db_name: str, *args: str) -> str:
    """Run psql against a database on the test database's server and return the query results.

    Args:
        db_name (str): Name of the database to connect to.
        *args (str): Further psql arguments.

    Returns:
        str: The query results only, one row per line, columns separated by "|".
    """
    command, env = connection.client.settings_to_cmd_args_env(
        {**connection.settings_dict, "NAME": db_name}, ["-v", "ON_ERROR_STOP=1", "-qAt", *args]
    )
    return subprocess.run(
        command, env={**os.environ, **(env or {})}, check=True, stdout=subprocess.PIPE, text=True
    ).stdout


@pytest.fixture
def restored_db_name() -> Iterator[str]:
    """Create an empty database to restore a dump into, and drop it afterwards."""
    db_name = f"{connection.settings_dict['NAME']}_restored"
    drop = f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'
    _psql("postgres", "-c", drop)
    _psql("postgres", "-c", f'CREATE DATABASE "{db_name}" TEMPLATE template0')
    yield db_name
    _psql("postgres", "-c", drop)


@pytest.mark.django_db(transaction=True)
def test_dump_and_restore_removes_personal_data(tmp_path: Path, restored_db_name: str) -> None:
    user = UserFactory(
        username=PERSONAL_DATA_MARKER,
        email=PERSONAL_EMAIL,
        first_name=PERSONAL_DATA_MARKER,
        last_name=PERSONAL_DATA_MARKER,
        department_name=PERSONAL_DATA_MARKER,
        additional_information=PERSONAL_DATA_MARKER,
    )
    sign = TrafficSignRealFactory(created_by=user, updated_by=user)
    Token.objects.create(user=user)
    session = SessionStore()
    session["secret"] = PERSONAL_EMAIL
    session.create()
    dump_path = tmp_path / "sanitized_db.sql"

    with dump_path.open("wb") as out:
        write_sanitized_dump(out)

    # Covers the user's columns and everything derived from them, such as the audit log entry of the user's creation.
    assert PERSONAL_DATA_MARKER.encode() not in dump_path.read_bytes()
    _psql(restored_db_name, f"--file={dump_path}")
    assert _psql(restored_db_name, "-c", "SELECT DISTINCT password FROM users_user") == "!\n"
    # The marker check cannot see these: session data is encoded and token keys are random.
    assert _psql(restored_db_name, "-c", "SELECT count(*) FROM authtoken_token") == "0\n"
    assert _psql(restored_db_name, "-c", "SELECT count(*) FROM django_session") == "0\n"
    signs = _psql(restored_db_name, "-c", "SELECT id, created_by_id FROM traffic_sign_real")
    assert signs == f"{sign.id}|{user.id}\n"


@pytest.mark.django_db(transaction=True)
def test_write_sanitized_dump_refuses_incomplete_rules(monkeypatch: pytest.MonkeyPatch) -> None:
    problems = {"tables without a rule": ["new_table"]}
    monkeypatch.setattr("traffic_control.services.sanitized_db_dump.rule_problems", lambda: problems)
    out = io.BytesIO()

    with pytest.raises(SanitizedDumpError, match="new_table"):
        write_sanitized_dump(out)

    assert out.getvalue() == b""
