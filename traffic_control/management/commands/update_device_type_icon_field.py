from django.core.management import BaseCommand
from django.db import transaction

from traffic_control.models.common import TrafficControlDeviceType, TrafficControlDeviceTypeIcon


class Command(BaseCommand):
    help = (
        "Point the file_field of existing TrafficControlDeviceType objects to the file corresponds to the icon string"
    )

    @transaction.atomic
    def handle(self, *_args, **_options):
        self.stdout.write("Updating TrafficControlDeviceType icon_file fields...")

        TrafficControlDeviceType.objects.count()
        updated_device_types = []
        bogus_device_types = []
        for device_type in TrafficControlDeviceType.objects.all():
            if not device_type.icon:
                self.stdout.write(f"Skipped TrafficControlDeviceType without icon string. Device type: {device_type}")
                continue

            if not device_type.icon.endswith(".svg"):
                bogus_device_types.append(device_type)
                continue

            try:
                # matching against "/bar.svg" is better because "bar.svg" can match ["bar.svg", "foobar.svg"]
                device_type.icon_file = TrafficControlDeviceTypeIcon.objects.get(file__endswith=f"/{device_type.icon}")
                updated_device_types.append(device_type)
            except TrafficControlDeviceTypeIcon.DoesNotExist:
                bogus_device_types.append(device_type)
                self.stderr.write(
                    self.style.ERROR(
                        f"TrafficControlDeviceTypeIcon '{device_type.icon}' not found. Device type: {device_type}"
                    )
                )

        TrafficControlDeviceType.objects.bulk_update(updated_device_types, ["icon_file"], batch_size=1000)

        if len(bogus_device_types) > 0:
            self.stderr.write(
                self.style.WARNING(f"{len(bogus_device_types)} TrafficControlDeviceType could not be updated")
            )
            for device_type in bogus_device_types:
                self.stderr.write(self.style.WARNING(f"\tIcon: '{device_type.icon}'. Device type: {device_type}"))

        self.stdout.write(self.style.SUCCESS(f"Updated {len(updated_device_types)} TrafficControlDeviceType objects."))
