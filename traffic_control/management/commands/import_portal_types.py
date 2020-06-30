import csv
import os

from django.core.management.base import BaseCommand, CommandError

from traffic_control.models import PortalType


class Command(BaseCommand):
    help = "Import portal types from a csv file"

    def add_arguments(self, parser):
        parser.add_argument("filename", help="Path to the portal types csv file")

    def handle(self, *args, **options):
        filename = options["filename"]
        if not os.path.exists(filename):
            raise CommandError(f"File {filename} does not exist")

        self.stdout.write("Importing portal types...")
        count = 0
        with open(filename) as f:
            csv_reader = csv.reader(f)
            next(csv_reader, None)  # skip header
            for row in csv_reader:
                structure, build_type, model = row
                _, created = PortalType.objects.get_or_create(
                    structure=structure, build_type=build_type, model=model
                )
                if created:
                    count += 1
        self.stdout.write(f"{count} portal types are imported")
