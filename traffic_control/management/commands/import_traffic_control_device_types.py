import csv
import os

from django.core.management.base import BaseCommand, CommandError

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import TrafficControlDeviceType


class Command(BaseCommand):
    help = "Import traffic control device types from a csv file"

    def add_arguments(self, parser):
        parser.add_argument("filename", help="Path to the traffic control device types csv file")

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
                (
                    code,
                    description,
                    icon,
                    value,
                    unit,
                    size,
                    legacy_code,
                    legacy_description,
                    type,
                    target_model,
                ) = row

                defaults = {
                    "icon": icon,
                    "description": description,
                    "value": value,
                    "unit": unit,
                    "size": size,
                    "legacy_code": legacy_code,
                    "legacy_description": legacy_description,
                    "type": type,
                }

                try:
                    device_type = TrafficControlDeviceType.objects.get(code=code)
                    for key, value in defaults.items():
                        setattr(device_type, key, value)
                    if not device_type.target_model:
                        # assign target_model when the target_model is None in current device type
                        device_type.target_model = DeviceTypeTargetModel[target_model.upper()] if target_model else ""
                    device_type.save(validate_target_model_change=False)
                except TrafficControlDeviceType.DoesNotExist:
                    defaults["code"] = code
                    # assign target_model when creating new traffic control device types
                    defaults["target_model"] = DeviceTypeTargetModel[target_model.upper()] if target_model else ""
                    TrafficControlDeviceType.objects.create(**defaults)

                count += 1
        self.stdout.write(f"{count} traffic control device types are imported")
