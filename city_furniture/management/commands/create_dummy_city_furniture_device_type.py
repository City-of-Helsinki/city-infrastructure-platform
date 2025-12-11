from city_furniture.enums import CityFurnitureClassType, CityFurnitureFunctionType
from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.models.common import CityFurnitureDeviceType
from traffic_control.management.commands.base_create_dummy_device_type import (
    BaseCreateDummyDeviceTypeCommand,
)


class Command(BaseCreateDummyDeviceTypeCommand):
    help = "Create a dummy city furniture device type and assign it to all devices with device_type=None"

    def get_model_choices(self):
        """Return list of model name choices for the --models parameter."""
        return [
            "FurnitureSignpostPlan",
            "FurnitureSignpostReal",
        ]

    def get_all_models(self):
        """Return list of all models that have device_type field."""
        return [
            ("FurnitureSignpostPlan", FurnitureSignpostPlan),
            ("FurnitureSignpostReal", FurnitureSignpostReal),
        ]

    def get_or_create_dummy_device_type(self, dry_run):
        """Create or get the dummy device type."""
        dummy_device_type, created = CityFurnitureDeviceType.objects.get_or_create(
            code="DummyDT",
            defaults={
                "description_fi": "Paikanpitäjä laitteille, joilla ei ole device_type asetettu",
                "description_en": "Placeholder for devices that have None set to device_type",
                "class_type": CityFurnitureClassType.OTHERS,
                "function_type": CityFurnitureFunctionType.FREE_STANDING_SIGN,
                "target_model": None,
            },
        )

        if created:
            if dry_run:
                self.stdout.write(self.style.SUCCESS("Would create dummy city furniture device type: DummyDT"))
                # Rollback the creation in dry-run mode
                dummy_device_type.delete()
                return None
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Created dummy city furniture device type: {dummy_device_type.code}")
                )
        else:
            self.stdout.write(
                self.style.WARNING(f"Dummy city furniture device type already exists: {dummy_device_type.code}")
            )

        return dummy_device_type

    def get_no_devices_message(self):
        """Return the message to display when no devices with device_type=None are found."""
        return "No city furniture devices with device_type=None found"

    def get_summary_message_prefix(self):
        """Return the prefix for the summary message."""
        return "city furniture device"
