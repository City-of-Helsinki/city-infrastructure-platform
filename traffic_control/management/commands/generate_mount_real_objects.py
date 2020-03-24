from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction

from traffic_control.models import MountReal, MountType, TrafficSignReal

OWNER = "Helsingin kaupunki"


class Command(BaseCommand):
    help = "Generate mount real objects from traffic sign real objects"

    def handle(self, *args, **options):
        self.stdout.write("Generating mount real objects ...")
        count = 0
        # main traffic signs are those whose legacy code
        # does not start with 8
        main_traffic_signs = TrafficSignReal.objects.filter(
            mount_real__isnull=True, mount_type__isnull=False
        ).exclude(legacy_code__startswith="8")
        for main_traffic_sign in main_traffic_signs:
            # wrapper MountReal object creation and traffic sign
            # linking in a transaction so that unlinked main traffic
            # signs and linked additional traffic signs can still be
            # found in a second run on failures
            with transaction.atomic():
                mount_real = MountReal.objects.create(
                    location=Point(
                        main_traffic_sign.location.x,
                        main_traffic_sign.location.x,
                        srid=settings.SRID,
                    ),
                    type=MountType[main_traffic_sign.mount_type.upper()].value,
                    owner=OWNER,
                    created_by=main_traffic_sign.created_by,
                    updated_by=main_traffic_sign.updated_by,
                )
                main_traffic_sign.mount_real = mount_real
                main_traffic_sign.save(update_fields=("mount_real",))
                main_traffic_sign.children.all().update(mount_real=mount_real)
            count += 1

        self.stdout.write(
            "Generating mount real objects completed. {0} mount real objects created.".format(
                count
            )
        )
