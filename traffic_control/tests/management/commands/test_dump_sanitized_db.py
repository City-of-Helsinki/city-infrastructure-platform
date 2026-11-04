import io
from typing import BinaryIO

import pytest
from django.core.management import call_command, CommandError

from traffic_control.services.sanitized_db_dump import SanitizedDumpError

WRITE_SANITIZED_DUMP = "traffic_control.management.commands.dump_sanitized_db.write_sanitized_dump"


@pytest.mark.django_db
def test_dump_sanitized_db_writes_dump_to_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    def write_dump(out: BinaryIO) -> None:
        out.write(b"BEGIN;\nCOMMIT;\n")

    monkeypatch.setattr(WRITE_SANITIZED_DUMP, write_dump)
    binary_stdout = io.BytesIO()
    # The command writes bytes to stdout.buffer, so stdout must be a text stream that wraps a binary one.
    stdout = io.TextIOWrapper(binary_stdout, write_through=True)

    call_command("dump_sanitized_db", stdout=stdout)

    assert binary_stdout.getvalue() == b"BEGIN;\nCOMMIT;\n"


@pytest.mark.django_db
def test_dump_sanitized_db_reports_failure_as_command_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(_out: BinaryIO) -> None:
        raise SanitizedDumpError("pg_dump of post-data failed with exit code 1.")

    monkeypatch.setattr(WRITE_SANITIZED_DUMP, fail)

    with pytest.raises(CommandError, match="pg_dump of post-data failed"):
        call_command("dump_sanitized_db")
