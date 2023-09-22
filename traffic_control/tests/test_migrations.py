from io import StringIO

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test__no_pending_migrations():
    """Ensure there are no pending migrations that should be generated."""
    out = StringIO()
    try:
        call_command(
            "makemigrations",
            "--dry-run",
            "--check",
            stdout=out,
            stderr=StringIO(),
        )
    except SystemExit as e:
        assert e.code == 0, out.getvalue()
