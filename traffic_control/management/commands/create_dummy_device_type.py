from traffic_control.management.commands.base_create_dummy_device_type import (
    BaseCreateDummyDeviceTypeCommand,
)
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    BarrierPlan,
    BarrierReal,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficControlDeviceType,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficSignPlan,
    TrafficSignReal,
)


class Command(BaseCreateDummyDeviceTypeCommand):
    help = "Create a dummy device type and assign it to all devices with device_type=None"

    def get_model_choices(self):
        """Return list of model name choices for the --models parameter."""
        return [
            "AdditionalSignPlan",
            "AdditionalSignReal",
            "BarrierPlan",
            "BarrierReal",
            "RoadMarkingPlan",
            "RoadMarkingReal",
            "SignpostPlan",
            "SignpostReal",
            "TrafficLightPlan",
            "TrafficLightReal",
            "TrafficSignPlan",
            "TrafficSignReal",
        ]

    def get_all_models(self):
        """Return list of all models that have device_type field."""
        return [
            ("AdditionalSignPlan", AdditionalSignPlan),
            ("AdditionalSignReal", AdditionalSignReal),
            ("BarrierPlan", BarrierPlan),
            ("BarrierReal", BarrierReal),
            ("RoadMarkingPlan", RoadMarkingPlan),
            ("RoadMarkingReal", RoadMarkingReal),
            ("SignpostPlan", SignpostPlan),
            ("SignpostReal", SignpostReal),
            ("TrafficLightPlan", TrafficLightPlan),
            ("TrafficLightReal", TrafficLightReal),
            ("TrafficSignPlan", TrafficSignPlan),
            ("TrafficSignReal", TrafficSignReal),
        ]

    def get_or_create_dummy_device_type(self, dry_run):
        """Create or get the dummy device type."""
        dummy_device_type, created = TrafficControlDeviceType.objects.get_or_create(
            code="DummyDT",
            defaults={
                "description": "Placeholder for devices that have None set to device_type",
                "target_model": None,
            },
        )

        if created:
            if dry_run:
                self.stdout.write(self.style.SUCCESS("Would create dummy device type: DummyDT"))
                # Rollback the creation in dry-run mode
                dummy_device_type.delete()
                return None
            else:
                self.stdout.write(self.style.SUCCESS(f"Created dummy device type: {dummy_device_type.code}"))
        else:
            self.stdout.write(self.style.WARNING(f"Dummy device type already exists: {dummy_device_type.code}"))

        return dummy_device_type

    def get_no_devices_message(self):
        """Return the message to display when no devices with device_type=None are found."""
        return "No devices with device_type=None found"

    def get_summary_message_prefix(self):
        """Return the prefix for the summary message."""
        return "device"
