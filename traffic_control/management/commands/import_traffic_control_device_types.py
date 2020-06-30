import csv
import os

from django.core.management.base import BaseCommand, CommandError

from traffic_control.models import TrafficControlDeviceType


class Command(BaseCommand):
    help = "Import traffic control device types from a csv file"

    def add_arguments(self, parser):
        parser.add_argument(
            "filename", help="Path to the traffic control device types csv file"
        )

    def handle(self, *args, **options):
        filename = options["filename"]
        if not os.path.exists(filename):
            raise CommandError(f"File {filename} does not exist")

        self.stdout.write("Importing traffic control device types...")
        count = 0
        with open(filename) as f:
            csv_reader = csv.reader(f)
            next(csv_reader, None)  # skip header
            for row in csv_reader:
                code, description, legacy_code, legacy_description, type = row
                TrafficControlDeviceType.objects.update_or_create(
                    code=code,
                    defaults={
                        "description": description,
                        "legacy_code": legacy_code,
                        "legacy_description": legacy_description,
                        "type": type,
                    },
                )
                count += 1
        self.stdout.write(f"{count} traffic control device types are imported")
