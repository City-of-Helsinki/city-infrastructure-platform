import os
from unittest.mock import mock_open, patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from traffic_control.models import PortalType


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

        # mock_open does not implement required dunder methods
        # in order to be consumable by csv.reader. There's an
        # open issue regarding this: https://bugs.python.org/issue21258
        m = mock_open(read_data=data)
        m.return_value.__iter__ = lambda f: f
        m.return_value.__next__ = lambda f: next(iter(f.readline, ""))

        with patch("traffic_control.management.commands.import_portal_types.open", m):
            call_command("import_portal_types", "test-data.csv")
            self.assertEqual(PortalType.objects.count(), 3)
