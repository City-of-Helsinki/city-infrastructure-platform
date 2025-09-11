import os

from django.apps import apps
from django.core.files.base import ContentFile, File
from django.core.management import BaseCommand, CommandError
from django.db import transaction

from traffic_control.models.common import TrafficControlDeviceTypeIcon


class Command(BaseCommand):
    help = (
        "Generate TrafficControlDeviceTypeIcon objects for svg icons in our static icon folder and upload the SVG "
        "icons (and their corresponding PNG icons) to blobstorage. Will overwrite existing objects in the blobstorage "
        "if those already exist."
    )

    @transaction.atomic
    def handle(self, *_args, **_options):
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
                with open(file_path, "rb") as svg_file:
                    self.stdout.write(f"Uploading {file_path}")
                    content = ContentFile(svg_file.read())
                    file = File(content, file_name)

                    try:
                        # matching against "/bar.svg" is better because "bar.svg" can match ["bar.svg", "foobar.svg"]
                        icon = TrafficControlDeviceTypeIcon.objects.get(file__endswith=f"/{file_name}")
                        icon.file = file
                        icon.save()
                        self.stdout.write(self.style.SUCCESS("Icon updated\n"))
                    except TrafficControlDeviceTypeIcon.DoesNotExist:
                        TrafficControlDeviceTypeIcon.objects.create(file=file)
                        self.stdout.write(self.style.SUCCESS("Icon created\n"))
            except Exception as error:
                self.stderr.write(self.style.ERROR(f"Upload failed - Reason: {error}\n"))
                faulty_icons.append(file_path)

        if len(faulty_icons) > 0:
            self.stderr.write(self.style.WARNING(f"Unable to upload {len(faulty_icons)} icons to blobstorage!"))
            for icon in faulty_icons:
                self.stderr.write(self.style.WARNING(f"\t{icon}"))

        self.stdout.write("Icon upload to blobstorage complete.")
