import csv
import os

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError

from users.utils import get_system_user

from ...models import ArrowDirection, RoadMarkingReal, TrafficControlDeviceType
from ...utils import get_default_owner

SOURCE_NAME = "main_streets_2014"

ARROW_DIRECTION_MAPPING = {
    "F": ArrowDirection.STRAIGHT,
    "K": ArrowDirection.RIGHT,
    "H": ArrowDirection.RIGHT_AND_STRAIGHT,
    "J": ArrowDirection.LEFT,
    "G": ArrowDirection.LEFT_AND_STRAIGHT,
    "L": ArrowDirection.LANE_ENDS,
    "VO": ArrowDirection.RIGHT_AND_LEFT,
    "Oarrow": ArrowDirection.STRAIGHT_RIGHT_AND_LEFT,
}


class Command(BaseCommand):
    help = "Import road marking reals from a csv file"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_types = {}

    def add_arguments(self, parser):
        parser.add_argument("filename", help="Path to the road marking csv file")

    def handle(self, *args, **options):
        filename = options["filename"]
        if not os.path.exists(filename):
            raise CommandError(f"File {filename} does not exist")

        self.stdout.write("Importing road markings...")
        count = 0
        user = get_system_user()
        owner = get_default_owner()
        with open(filename) as f:
            csv_reader = csv.reader(f, delimiter=";")
            next(csv_reader, None)  # skip header
            for row in csv_reader:
                (
                    source_id,
                    x,
                    y,
                    device_type_code,
                    arrow_direction,
                    size,
                    color,
                    additional_info,
                    value,
                ) = row
                RoadMarkingReal.objects.update_or_create(
                    source_name=SOURCE_NAME,
                    source_id=source_id,
                    defaults={
                        "location": Point(int(x), int(y), srid=settings.SRID),
                        "device_type": self.get_device_type(device_type_code),
                        "arrow_direction": ARROW_DIRECTION_MAPPING.get(arrow_direction),
                        "size": size,
                        "color": color,
                        "additional_info": additional_info,
                        "value": value,
                        "created_by": user,
                        "updated_by": user,
                        "owner": owner,
                    },
                )
                count += 1
        self.stdout.write(f"{count} road markings are imported")

    def get_device_type(self, device_type_code):
        if device_type_code not in self.device_types:
            device_type = TrafficControlDeviceType.objects.get(code=device_type_code)
            self.device_types[device_type_code] = device_type
        return self.device_types[device_type_code]
