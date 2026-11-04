"""SQL dump of the database with personal data replaced or left out.

What is kept, excluded and scrubbed is defined in ``traffic_control/services/sanitized_db_dump_rules.py``.
The ``dump_sanitized_db`` management command runs ``write_sanitized_dump`` on the pod.
"""

import os
import shutil
import subprocess
from typing import BinaryIO

from django.db import connection, transaction
from django.db.backends.utils import CursorWrapper

from traffic_control.services.sanitized_db_dump_rules import (
    ColumnRule,
    EXCLUDE_DATA_TABLES,
    KEEP,
    rule_problems,
    SCRUB_TABLES,
)


class SanitizedDumpError(Exception):
    """The sanitized dump could not be made."""


def write_sanitized_dump(out: BinaryIO) -> None:
    """Write a sanitized SQL dump of the database.

    Reads the database in one read-only transaction. Nothing is written if the rules are incomplete.

    Args:
        out (BinaryIO): Binary stream to write the dump to.

    Returns:
        None

    Raises:
        SanitizedDumpError: If the rules do not classify the database completely, or if pg_dump fails.
    """
    # The rule check, pg_dump and the scrubbed tables read from one snapshot.
    with transaction.atomic(durable=True), connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        cursor.execute("SELECT pg_export_snapshot()")
        snapshot = cursor.fetchone()[0]
        if problems := rule_problems():
            raise SanitizedDumpError(
                f"The rules do not classify the database completely: {problems}. Update "
                "traffic_control/services/sanitized_db_dump_rules.py."
            )

        out.write(b"BEGIN;\n")
        _pg_dump(out, snapshot, "pre-data", "data")
        for table, columns in SCRUB_TABLES.items():
            _copy_scrubbed_table(cursor, out, table, columns)
        # Indexes and foreign keys come last: they can be built only when the scrubbed rows are in place.
        _pg_dump(out, snapshot, "post-data")
        out.write(b"COMMIT;\n")


def _copy_scrubbed_table(cursor: CursorWrapper, out: BinaryIO, table: str, columns: dict[str, ColumnRule]) -> None:
    """Append the rows of a scrubbed table as a COPY statement, with the replaced columns' values replaced.

    Args:
        cursor (CursorWrapper): Cursor inside the dump's transaction.
        out (BinaryIO): Binary stream to write to.
        table (str): Name of the scrubbed table.
        columns (dict[str, ColumnRule]): Every column of the table, mapped to KEEP or its replacing SQL expression.

    Returns:
        None
    """
    quote = connection.ops.quote_name
    column_names = ", ".join(quote(column) for column in columns)
    select_list = ", ".join(
        quote(column) if rule is KEEP else f"{rule} AS {quote(column)}" for column, rule in columns.items()
    )
    out.write(f"COPY public.{quote(table)} ({column_names}) FROM stdin;\n".encode())
    cursor.copy_expert(f"COPY (SELECT {select_list} FROM public.{quote(table)}) TO STDOUT", out)
    out.write(b"\\.\n\n")


def _pg_dump(out: BinaryIO, snapshot: str, *sections: str) -> None:
    """Append the given pg_dump sections, leaving out the data of excluded and scrubbed tables.

    Args:
        out (BinaryIO): Binary stream to write to.
        snapshot (str): Exported snapshot that pg_dump reads from.
        *sections (str): Names of the pg_dump sections to append.

    Returns:
        None

    Raises:
        SanitizedDumpError: If pg_dump fails.
    """
    psql_command, env = connection.client.settings_to_cmd_args_env(
        connection.settings_dict,
        [
            "--no-owner",
            "--no-privileges",
            f"--snapshot={snapshot}",
            *(f"--section={section}" for section in sections),
            *(f"--exclude-table-data={table}" for table in sorted(EXCLUDE_DATA_TABLES | SCRUB_TABLES.keys())),
        ],
    )
    # pg_dump takes psql's connection options. The password is in the environment, out of the process list.
    with subprocess.Popen(
        ["pg_dump", *psql_command[1:]], stdout=subprocess.PIPE, env={**os.environ, **(env or {})}
    ) as process:
        shutil.copyfileobj(process.stdout, out)
    if process.returncode != 0:
        raise SanitizedDumpError(f"pg_dump of {', '.join(sections)} failed with exit code {process.returncode}.")
