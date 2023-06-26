import random

from django.core.management.base import BaseCommand
from django.db import transaction

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.factories import TrafficSignRealFactory
from traffic_control.models import Owner
from traffic_control.models.common import TrafficControlDeviceType


class Command(BaseCommand):
    help = "Generates test data"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Generating data...")

        owners = Owner.objects.all()
        device_types = TrafficControlDeviceType.objects.filter(target_model=DeviceTypeTargetModel.TRAFFIC_SIGN)

        for _ in range(5):
            owner = random.choice(owners)

            has_device_type = random.randint(0, 100) < 95
            device_type = random.choice(device_types) if has_device_type else None

            TrafficSignRealFactory(
                owner=owner,
                device_type=device_type,
            )
