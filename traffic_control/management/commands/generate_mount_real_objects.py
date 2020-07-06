from itertools import chain

from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.management.base import BaseCommand
from django.db import transaction

from traffic_control.models import AdditionalSignReal, MountReal, TrafficSignReal

OWNER = "Helsingin kaupunki"


class Command(BaseCommand):
    help = "Generate mount real objects from traffic sign real objects"

    def add_arguments(self, parser):
        parser.add_argument(
            "-r",
            "--radius",
            type=float,
            default=1,
            help="Search radius for existing mount real",
        )

    def handle(self, *args, **options):
        self.stdout.write("Generating mount real objects ...")
        traffic_signs = TrafficSignReal.objects.active().filter(
            mount_real__isnull=True, mount_type__isnull=False
        )

        standalone_additional_signs = AdditionalSignReal.objects.active().filter(
            mount_real__isnull=True, mount_type__isnull=False, parent__isnull=True
        )

        for traffic_sign in list(chain(traffic_signs, standalone_additional_signs)):
            # wrap MountReal object creation and traffic sign
            # linking in a transaction so that unlinked main traffic
            # signs and linked additional traffic signs can still be
            # found in a second run on failures
            with transaction.atomic():
                mount_real = self.get_mount_real(traffic_sign, options["radius"])
                traffic_sign.mount_real = mount_real
                traffic_sign.save(update_fields=("mount_real",))
                if isinstance(traffic_sign, TrafficSignReal):
                    traffic_sign.additional_signs.active().update(mount_real=mount_real)

        self.stdout.write("Generating mount real objects completed.")

    def get_mount_real(self, traffic_sign, radius):
        """Get mount real object for traffic sign

        Return the mount real if there exists one with the same
        mount type within given radius, otherwise create new
        mount real object using the same location (x, y) as the
        traffic sign
        """
        mount_real = (
            MountReal.objects.active()
            .filter(
                location__dwithin=(traffic_sign.location, D(m=radius)),
                mount_type=traffic_sign.mount_type,
            )
            .first()
        )
        if not mount_real:
            mount_real = MountReal.objects.create(
                location=Point(
                    traffic_sign.location.x,
                    traffic_sign.location.y,
                    srid=settings.SRID,
                ),
                mount_type=traffic_sign.mount_type,
                owner=OWNER,
                created_by=traffic_sign.created_by,
                updated_by=traffic_sign.updated_by,
            )
        return mount_real
