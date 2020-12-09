import os
import re
from decimal import Decimal, InvalidOperation

from dateutil.parser import parse
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError
from pytz import timezone

from users.utils import get_system_user

from ...models import (
    AdditionalSignContentReal,
    AdditionalSignReal,
    MountType,
    TrafficSignReal,
)
from ...utils import get_default_owner

CLI_HELP_TEXT = """
Import traffic sign real data to the platform from standard ESRI SHP-file.

Note that SHP-metadata and related files (.shp, .shx, .dbf, .prj, .qix, .cpg)
need to also exist the same directory.

Shapefile is expected to have a single layer with PointZ geometries and following attributes:
    fid:String
    type:String
    text:String
    mount_type:String
    direction:String
    date:String
"""

TARGET_SRID = 3879
SOURCE_NAME = "BLOM streetview2019"


class Command(BaseCommand):
    help = CLI_HELP_TEXT

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--filename",
            required=True,
            type=str,
            help="Path to the traffic sign reals SHP-file",
        )

    def get_date(self, feature):
        date_str = str(feature.get("date"))
        tz = timezone(settings.TIME_ZONE)
        return tz.localize(parse(date_str))

    def get_location(self, feature, source_srid):
        """
        Get Point instance representing feature's coordinates

        Transform the point to correct SRID used in platform if necessary
        """
        location = Point(
            x=float(str(feature["x"])),
            y=float(str(feature["y"])),
            z=float(str(feature["z"])),
            srid=source_srid,
        )
        if source_srid != TARGET_SRID:
            location.transform(TARGET_SRID)

        return location

    def get_mount_type(self, feature):
        """
        Get MountType object for feature's mount_type string
        """
        mount_type = str(feature.get("mount_type"))

        if not feature.get("mount_type"):
            return None

        try:
            return MountType.objects.get(code=mount_type.upper())
        except MountType.DoesNotExist:
            return MountType.objects.create(
                code=mount_type.upper(), description=mount_type.capitalize()
            )

    def handle(self, *args, **options):
        filename = options["filename"]
        if not os.path.exists(filename):
            raise CommandError("File {0} does not exist".format(filename))

        user = get_system_user()
        owner = get_default_owner()

        data_source = DataSource(filename)
        layer = data_source[0]
        source_srid = layer.srs.srid
        feature_count = len(layer)

        self.stdout.write(f"SHP-file has {feature_count} features.")

        counter = 0
        additional_sign_counter = 0

        for feature in layer:
            legacy_code = str(feature.get("type")).strip()
            is_additional_sign = legacy_code.startswith("8")
            traffic_sign_model = (
                AdditionalSignReal if is_additional_sign else TrafficSignReal
            )

            data = {
                "location": self.get_location(feature, source_srid),
                "legacy_code": legacy_code,
                "direction": int(str(feature.get("direction") or 0)),
                "scanned_at": self.get_date(feature),
                "mount_type": self.get_mount_type(feature),
                "owner": owner,
                "created_by": user,
                "updated_by": user,
            }

            # Add text to the sign data if the imported sign is not an additional sign
            text = str(feature.get("text") or "").strip()
            if not is_additional_sign and text:
                data["txt"] = text
                data["value"] = self.extract_numeric_value(text)

            obj, created = traffic_sign_model.objects.update_or_create(
                source_name=SOURCE_NAME,
                source_id=str(feature.get("fid")),
                defaults=data,
            )

            # Create content instance for additional sign that contains the sign text
            if is_additional_sign and text:
                AdditionalSignContentReal.objects.update_or_create(
                    source_name=SOURCE_NAME,
                    source_id=str(feature.get("fid")),
                    defaults={
                        "parent": obj,
                        "text": text,
                        "order": 1,
                        "created_by": user,
                        "updated_by": user,
                    },
                )

            counter += 1
            if is_additional_sign:
                additional_sign_counter += 1

            if counter % 100 == 0:
                self.stdout.write(f"{counter} traffic signs imported...")

        self.stdout.write(
            f"{counter} traffic signs imported of which "
            f"{additional_sign_counter} are additional signs"
        )
        self.stdout.write("Import done!")

    def extract_numeric_value(self, text):
        """
        Extract numeric value from text. If there are multiple numeric
        values in the text, return the first one. Return None if no
        numeric values found
        """
        pattern = "[\d.,-]+"
        numbers = re.findall(pattern, text)
        if not numbers:
            return None
        try:
            value_str = numbers[0].replace(",", ".")
            return Decimal(value_str)
        except InvalidOperation:
            self.stdout.write(f"Cannot convert to decimal: {value_str}")
            return None
