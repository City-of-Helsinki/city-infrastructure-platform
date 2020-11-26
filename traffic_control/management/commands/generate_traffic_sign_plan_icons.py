import os
from xml.etree.ElementTree import parse

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate traffic sign plan icons from traffic sign real icons"
    ns = {"": "http://www.w3.org/2000/svg"}
    opacity = "0.6"

    def handle(self, *args, **options):
        self.stdout.write("Generating traffic sign plan icons...")
        svg_dir = os.path.join(
            settings.BASE_DIR, "traffic_control/static/traffic_control/svg"
        )
        src_dir = os.path.join(svg_dir, "traffic_sign_icons")
        dest_dir = os.path.join(svg_dir, "traffic_sign_plan_icons")
        filenames = os.listdir(src_dir)
        for filename in filenames:
            src_file = os.path.join(src_dir, filename)
            dest_file = os.path.join(dest_dir, filename)
            self.create_traffic_sign_plan_icon(src_file, dest_file)
        self.stdout.write("Generating traffic sign plan icons completed")

    def create_traffic_sign_plan_icon(self, src_file, dest_file):
        self.stdout.write(f"Processing {src_file}...")
        tree = parse(src_file)
        root = tree.getroot()
        root.set("opacity", self.opacity)
        tree.write(dest_file, default_namespace="")
