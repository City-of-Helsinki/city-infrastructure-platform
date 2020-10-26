import csv
import os

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError

from users.utils import get_system_user

from ...models import AdditionalSignContentReal, AdditionalSignReal, TrafficSignReal
from ...models.traffic_sign import LocationSpecifier
from ...utils import get_default_owner

SOURCE_NAME = "Vaisala 2019-2020"
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
        owner = get_default_owner()
        with open(filename, encoding="utf-8-sig") as f:
            csv_reader = csv.DictReader(f, delimiter=",")
            for row in csv_reader:
                location = Point(
                    float(row["longitude"]), float(row["latitude"]), 0, srid=SOURCE_SRID
                )
                location.transform(settings.SRID)
                is_additional_sign = row["code"].strip().startswith("8")
                traffic_sign_model = (
                    AdditionalSignReal if is_additional_sign else TrafficSignReal
                )
                traffic_sign, _ = traffic_sign_model.objects.update_or_create(
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
                        "owner": owner,
                        "created_by": user,
                        "updated_by": user,
                    },
                )
                count += 1

                if is_additional_sign:
                    AdditionalSignContentReal.objects.create(
                        parent=traffic_sign,
                        text=row["text"],
                        order=1,
                        created_by=user,
                        updated_by=user,
                    )

                if count % self.step == 0:
                    self.stdout.write(f"{count} traffic signs are imported...")

        self.stdout.write(f"{count} traffic signs are imported")
