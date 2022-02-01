import csv
import os

from django.core.management.base import BaseCommand, CommandError

from city_furniture.enums import CityFurnitureDeviceTypeTargetModel
from city_furniture.models.common import CityFurnitureDeviceType


class Command(BaseCommand):
    help = "Import City Furniture Device Types from a csv file"

    def add_arguments(self, parser):
        parser.add_argument(
            "filename",
            nargs="?",
            type=str,
            help="Path to the City Furniture Device Types csv file",
            default="./city_furniture/data/city_furniture_device_types.csv",
        )

    def handle(self, *args, **options):
        filename = options["filename"]
        if not os.path.exists(filename):
            raise CommandError(f"File {filename} does not exist")

        self.stdout.write("Importing city furniture device types...")
        count = 0
        with open(filename) as f:
            csv_reader = csv.reader(f)
            next(csv_reader, None)  # skip header
            for row in csv_reader:
                (code, class_type, function_type, icon, description, size, target_model) = row

                defaults = {
                    "code": code,
                    "class_type": class_type,
                    "function_type": function_type,
                    "icon": icon,
                    "description": description,
                    "size": size,
                    "target_model": target_model,
                }

                try:
                    device_type = CityFurnitureDeviceType.objects.get(code=code)
                    for key, value in defaults.items():
                        setattr(device_type, key, value)
                    if not device_type.target_model:
                        # assign target_model when the target_model is None in current device type
                        device_type.target_model = (
                            CityFurnitureDeviceTypeTargetModel[target_model.upper()] if target_model else ""
                        )
                    device_type.save(validate_target_model_change=False)
                except CityFurnitureDeviceType.DoesNotExist:
                    defaults["code"] = code
                    # assign target_model when creating new traffic control device types
                    defaults["target_model"] = (
                        CityFurnitureDeviceTypeTargetModel[target_model.upper()] if target_model else ""
                    )
                    CityFurnitureDeviceType.objects.create(**defaults)

                count += 1
        self.stdout.write(f"{count} traffic control device types are imported")
