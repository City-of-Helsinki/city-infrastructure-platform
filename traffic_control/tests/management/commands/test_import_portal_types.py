import pytest
from django.core.management import call_command, CommandError

from traffic_control.models import PortalType


@pytest.mark.django_db
def test_raise_command_error_if_no_file_found():
    with pytest.raises(CommandError):
        call_command("import_portal_types", "dummy.csv")


@pytest.mark.django_db
def test_import_portal_types_success(datadir):
    call_command("import_portal_types", datadir / "success.csv")
    assert PortalType.objects.count() == 3
