from io import StringIO

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_command_execution():
    out = StringIO()
    call_command("list_admin_models", stdout=out)
    output = out.getvalue()

    hr = "-" * 40
    # Check for the presence of some entries that are likely to remain present and unchanged as the project progresses
    assert f"App: auditlog\n{hr}\n  Model: LogEntry" in output
    assert f"App: authtoken\n{hr}\n  Model: TokenProxy\n  Admin: rest_framework.authtoken.admin.TokenAdmin" in output
    assert f"App: users\n{hr}\n  Model: User\n  Admin: users.admin.UserAdmin" in output
