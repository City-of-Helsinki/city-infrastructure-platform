from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.management.base import BaseCommand

from traffic_control.models import AdditionalSignReal, TrafficSignReal


class Command(BaseCommand):
    help = "Link additional traffic signs to main traffic signs"

    def add_arguments(self, parser):
        parser.add_argument(
            "-r",
            "--radius",
            type=float,
            default=1,
            help="Search radius in meters",
        )

    def handle(self, *args, **options):
        self.stdout.write("Linking additional traffic signs ...")
        count = 0
        # The legacy code (type column from shapefile data) of the traffic signs follows
        # certain patterns. The legacy code of additional traffic signs always starts with
        # 8. See details with: https://vayla.fi/web/en/road-network/traffic-signs/additional-panels
        additional_sign_qs = AdditionalSignReal.objects.active().filter(parent__isnull=True)
        for additional_sign in additional_sign_qs:
            # find nearby main traffic sign candidates that have the same
            # mount type as target additional traffic sign
            main_signs = TrafficSignReal.objects.active().filter(
                mount_type=additional_sign.mount_type,
                location__dwithin=(additional_sign.location, D(m=options["radius"])),
            )

            # find the main traffic sign that appears immediately above the target
            # i.e. the main traffic sign has bigger z coordinate but a minimum z
            # coordinate difference compared to target additional traffic sign
            parent_main_sign = None
            min_z_diff = None
            for main_sign in main_signs:
                diff_z = main_sign.location.z - additional_sign.location.z
                if min_z_diff is None or min_z_diff > diff_z > 0:
                    parent_main_sign = main_sign
                    min_z_diff = diff_z

            # assign the found main traffic sign to the target additional traffic sign,
            # and update additional traffic sign to use same x,y coordinates as the
            # main traffic sign if found
            if parent_main_sign:
                additional_sign.parent = parent_main_sign
                additional_sign.location = Point(
                    parent_main_sign.location.x,
                    parent_main_sign.location.y,
                    additional_sign.location.z,
                    srid=settings.SRID,
                )
                additional_sign.save(update_fields=("parent", "location"))
                count += 1

        self.stdout.write(
            "Linking additional traffic signs completed. {0} additional traffic signs linked.".format(count)
        )
