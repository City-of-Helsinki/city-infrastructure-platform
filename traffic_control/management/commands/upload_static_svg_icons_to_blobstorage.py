import os

from auditlog.context import set_actor
from django.apps import apps
from django.core.files.base import ContentFile, File
from django.core.management import BaseCommand, CommandError
from django.db import transaction

from traffic_control.models.common import TrafficControlDeviceTypeIcon
from users.utils import get_system_user


class Command(BaseCommand):
    help = (
        "Generate TrafficControlDeviceTypeIcon objects for svg icons in our static icon folder and upload the SVG "
        "icons (and their corresponding PNG icons) to blobstorage. Will overwrite existing objects in the blobstorage "
        "if those already exist."
    )

    @transaction.atomic
    def handle(self, *_args, **_options):
        with set_actor(get_system_user()):
            self.stdout.write("Uploading SVG files to blobstorage...")

            svg_directory = os.path.join(
                apps.get_app_config("traffic_control").path, "static", "traffic_control", "svg", "traffic_sign_icons"
            )
            if not os.path.isdir(svg_directory):
                raise CommandError(self.style.ERROR(f"Error: Static SVG folder no found in {svg_directory}"))

            faulty_icons = []
            for file_name in os.listdir(svg_directory):
                if not file_name.endswith(".svg"):
                    self.stdout.write(f"Skipped {file_name}...")
                    continue

                file_path = os.path.join(svg_directory, file_name)
                try:
                    self.upload_icon_file(file_path=file_path, file_name=file_name)
                except Exception as error:
                    self.stderr.write(self.style.ERROR(f"Upload failed - Reason: {error}\n"))
                    faulty_icons.append(file_path)

            if len(faulty_icons) > 0:
                self.stderr.write(self.style.WARNING(f"Unable to upload {len(faulty_icons)} icons to blobstorage!"))
                for icon in faulty_icons:
                    self.stderr.write(self.style.WARNING(f"\t{icon}"))

            self.stdout.write("Icon upload to blobstorage complete.")

    def upload_icon_file(self, *, file_path: str, file_name: str):
        """Upload the SVG ile to the cloud and assign it to the corresponding TrafficControlDeviceTypeIcon file field.

        Will update the corresponding TrafficControlDeviceTypeIcon objects or create new ones if none exist.

        Args:
              file_path (str): Full path to the SVG file in the local disk (including file name).
              file_name (str): Just the file name)
        """
        with open(file_path, "rb") as svg_file:
            self.stdout.write(f"Uploading {file_path}")
            content = ContentFile(svg_file.read())
            file = File(content, file_name)

            # matching against "/bar.svg" is better because "bar.svg" can match "bar.svg", "foobar.svg"
            _, icon_created = TrafficControlDeviceTypeIcon.objects.update_or_create(
                file__endswith=f"/{file_name}", defaults={"file": file}
            )
            if icon_created:
                self.stdout.write(self.style.SUCCESS("Icon created\n"))
            else:
                self.stdout.write(self.style.SUCCESS("Icon updated\n"))
