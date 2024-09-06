import pprint

from django.core.management.base import BaseCommand

from traffic_control.analyze_utils.traffic_sign_data import TrafficSignAnalyzer, TrafficSignImporter


class Command(BaseCommand):
    help = "Analyzes sign input data"

    def add_arguments(self, parser):
        parser.add_argument(
            "-mf",
            "--mount-file",
            type=str,
            help="Path to the mount file in csv format",
        )
        parser.add_argument(
            "-sf",
            "--sign-file",
            type=str,
            help="Path to the sign file in csv format",
        )
        parser.add_argument(
            "-u",
            "--update",
            action="store_true",
            dest="update",
            default=False,
            help="Try to update existing signs",
        )

    def handle(self, *args, **options):
        mount_file = options["mount_file"]
        if mount_file is None:
            self.stderr.write(self.style.ERROR("Missing mount file"))
            return None
        sign_file = options["sign_file"]
        if sign_file is None:
            self.stderr.write(self.style.ERROR("Missing sign file"))
            return None

        analyzer = TrafficSignAnalyzer(mount_file, sign_file)
        importer = TrafficSignImporter(
            analyzer.mounts_by_id, analyzer.signs_by_id, analyzer.additional_signs_by_id, options["update"]
        )
        results = importer.import_data()
        pprint.pprint(results)
