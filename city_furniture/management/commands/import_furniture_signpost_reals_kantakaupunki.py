import csv
import os
from datetime import datetime
from functools import lru_cache

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import atomic

from city_furniture.models import FurnitureSignpostReal
from city_furniture.models.common import CityFurnitureColor, CityFurnitureDeviceType, CityFurnitureTarget
from city_furniture.models.furniture_signpost import ArrowDirection
from traffic_control.models import MountType
from traffic_control.utils import get_default_owner
from users.utils import get_system_user

SOURCE_NAME = "Kantakaupungin Rantareitti 2022 csv"


class Command(BaseCommand):
    help = "Import Kantakaupungin Rantareitti Furniture Signpost reals from a csv file"
    step = 1000
    user = get_system_user()
    owner = get_default_owner()
    target = CityFurnitureTarget.objects.get_or_create(name_fi="Kantakaupungin Rantareitti")[0]
    new_mount_types = {
        "Ristikkopylväs": {
            "code": "LATTICECOLUMN",
            "description": "Lattice column",
            "description_fi": "Ristikkopylväs",
        },
        "Katuvalopylväs": {
            "code": "STREETLIGHTPOLE",
            "description": "Street light pole",
            "description_fi": "Katuvalopylväs",
        },
        "Tolppa": {  # Should already exist with a different description_fi value
            "code": "POLE",
            "description": "Pole",
            "description_fi": "Opaste",
        },
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "filename",
            nargs="?",
            type=str,
            help="Path to the Kantakaupungin rantareitti furniture signpost reals csv file",
            default="opastus_tietomalli.csv",
        )

    @lru_cache()
    def get_device_type(self, signpost_type: str) -> CityFurnitureDeviceType:
        signpost_types = {
            "reittivahvennelaatta": "Rantareitti-1A",
            "tarrat": "Rantareitti-2A",
            "pollarit": "Rantareitti-3",
            "kartat": "Rantareitti-4A",
            "viitat": "Rantareitti-5",
        }
        return CityFurnitureDeviceType.objects.get(code=signpost_types[signpost_type])

    @lru_cache()
    def get_mount_type(self, mount_type: str) -> MountType:
        """Get mount type for Furniture Signpost by description_fi, if it's a new type then it's created instead"""
        if mount_type in self.new_mount_types:
            return MountType.objects.get_or_create(
                description_fi=self.new_mount_types[mount_type]["description_fi"],
                defaults=dict(
                    code=self.new_mount_types[mount_type]["code"],
                    description=self.new_mount_types[mount_type]["description"],
                ),
            )[0]
        return MountType.objects.get(description_fi=mount_type)

    @lru_cache()
    def get_color(self, sign_color: str) -> CityFurnitureColor:
        return CityFurnitureColor.objects.get(name=sign_color)

    def str_to_date(self, date_str: str) -> datetime.date:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%d.%m.%Y")
            except ValueError:
                return datetime.strptime(date_str, "%m/%d/%y")

    def import_row_signpost(self, row):
        location = Point(float(row["latitude"]), float(row["longitude"]), 0, srid=settings.SRID)
        device_type = self.get_device_type(row["device_type"])

        signpost, created = FurnitureSignpostReal.objects.update_or_create(
            source_name=SOURCE_NAME,
            source_id=f"{row['id']}-{device_type.code}",
            device_type=device_type,
            defaults={
                "location": location,
                "owner": self.owner,
                "target": self.target,
                "location_name_fi": row["location_name_fi"],
                "direction": int(row["direction"]) if row["direction"] else 0,
                "height": int(row["height"]) if row["height"] else None,
                "mount_type": self.get_mount_type(row["mount_type"]) if row["mount_type"] else None,
                "arrow_direction": ArrowDirection[row["arrow_direction"]] if row["arrow_direction"] else None,
                "color": self.get_color(row["sign_color"]) if row["sign_color"] else None,
                "pictogram": row["pictogram"],
                "value": int(row["value"]) if row["value"] else None,
                "text_content_fi": row["text_content_fi"],
                "text_content_sw": row["text_content_sw"],
                "text_content_en": row["text_content_en"],
                "content_responsible_entity": row["content_responsible_entity"],
                "validity_period_start": (
                    self.str_to_date(row["validity_period_start"]) if row["validity_period_start"] else None
                ),
                "validity_period_end": (
                    self.str_to_date(row["validity_period_end"]) if row["validity_period_end"] else None
                ),
                "additional_material_url": row["additional_material_url"],
                "created_by": self.user,
                "updated_by": self.user,
                "source_name": SOURCE_NAME,
            },
        )
        return created

    @atomic
    def handle(self, *args, **options):
        filename = options["filename"]
        if not os.path.exists(filename):
            raise CommandError(f"File {filename} does not exist")

        self.stdout.write("Importing Kantakaupungin Rantareitti Furniture Signposts...")
        count = 0

        with open(filename, encoding="utf-8-sig") as f:
            csv_reader = csv.DictReader(f, delimiter=",")
            for row in csv_reader:
                created = self.import_row_signpost(row)
                if created:
                    count += 1

                if count % self.step == 0:
                    self.stdout.write(f"{count} traffic signs are imported...")

        self.stdout.write(f"{count} traffic signs are imported")
