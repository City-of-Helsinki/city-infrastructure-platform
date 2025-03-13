from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from traffic_control.analyze_utils.additional_sign_info_enrich import (
    do_database_update,
    get_error_infos,
    get_success_infos,
    get_update_infos,
)
from traffic_control.models import ParkingZoneUpdateInfo


class Command(BaseCommand):
    help = "Update AdditionalSignReal additional_information field. Also json schema updated if that can be done."

    def add_arguments(self, parser):
        parser.add_argument(
            "-u",
            "--update",
            action="store_true",
            dest="update",
            default=False,
            help="Actually do updates on the AdditionalSignReals",
        )

    def handle(self, *args, **options):
        start_time = datetime.now(timezone.utc)
        update_infos = get_update_infos()
        update_errors = get_error_infos(update_infos)
        update_success = get_success_infos(update_infos)

        if options["update"]:
            self.stdout.write("Updating additional_informations and schemas..")
            do_database_update(update_success, update_errors)
        else:
            self.stdout.write("Checking what to update...")
            end_time = datetime.now(timezone.utc)
            ParkingZoneUpdateInfo.objects.create(
                start_time=start_time,
                end_time=end_time,
                update_infos=update_success,
                update_errors=update_errors,
                database_update=False,
            )
