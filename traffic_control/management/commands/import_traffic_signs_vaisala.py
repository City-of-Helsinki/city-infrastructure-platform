import csv
import os

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError

from traffic_control.models import TrafficSignReal
from traffic_control.models.traffic_sign import LocationSpecifier
from users.utils import get_system_user

SOURCE_NAME = "Vaisala 2019-2020"
OWNER = "Helsingin kaupunki"
SOURCE_SRID = 4326


class Command(BaseCommand):
    help = "Import vaisala traffic signs from a csv file"
    step = 1000

    def add_arguments(self, parser):
        parser.add_argument(
            "filename", help="Path to the vaisala traffic sign csv file"
        )

    def handle(self, *args, **options):
        filename = options["filename"]
        if not os.path.exists(filename):
            raise CommandError(f"File {filename} does not exist")

        self.stdout.write("Importing vaisala traffic signs...")
        count = 0
        user = get_system_user()
        with open(filename, encoding="utf-8-sig") as f:
            csv_reader = csv.DictReader(f, delimiter=",")
            for row in csv_reader:
                location = Point(
                    float(row["longitude"]), float(row["latitude"]), 0, srid=SOURCE_SRID
                )
                location.transform(settings.SRID)
                TrafficSignReal.objects.update_or_create(
                    source_name=SOURCE_NAME,
                    source_id=row["id"],
                    defaults={
                        "location": location,
                        "legacy_code": row["code"],
                        "direction": row["heading"] or 0,
                        "scanned_at": row["last_detected"],
                        "location_specifier": LocationSpecifier[row["side"].upper()],
                        "operation": row["action"],
                        "attachment_url": row["frame_url"],
                        "source_id": row["id"],
                        "source_name": SOURCE_NAME,
                        "owner": OWNER,
                        "created_by": user,
                        "updated_by": user,
                    },
                )
                count += 1
                if count % self.step == 0:
                    self.stdout.write(f"{count} traffic signs are imported...")

        self.stdout.write(f"{count} traffic signs are imported")
