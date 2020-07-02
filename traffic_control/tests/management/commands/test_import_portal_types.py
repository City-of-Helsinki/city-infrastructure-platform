import os
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from traffic_control.models import PortalType

from .utils import mock_open


class ImportPortalTypesTestCase(TestCase):
    def test_raise_command_error_if_no_file_found(self):
        self.assertRaises(
            CommandError, call_command, "import_portal_types", "dummy.csv"
        )

    @patch("os.path.exists", return_value=True)
    def test_import_portal_types_success(self, mock_exists):
        data = os.linesep.join(
            [
                "Rakenne,Tyyppi,Malli",
                "Putki,kehä,tyyppi I",
                "Putki,korkea uloke,tyyppi UK I",
                "Ristikko,kehä,tyyppi R1",
                "Ristikko,kehä,tyyppi R1",
                "Ristikko,kehä,tyyppi R1",
            ]
        )

        with patch(
            "traffic_control.management.commands.import_portal_types.open",
            mock_open(read_data=data),
        ):
            call_command("import_portal_types", "test-data.csv")
            self.assertEqual(PortalType.objects.count(), 3)
