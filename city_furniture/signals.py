import logging
import os

import cairosvg
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models.signals import post_save
from django.dispatch import receiver

from city_furniture.models.common import CityFurnitureDeviceTypeIcon

logger = logging.getLogger("django")
logger.setLevel(logging.INFO)


@receiver(post_save, sender=CityFurnitureDeviceTypeIcon)
def generate_pngs_on_svg_save(instance, created, **_kwargs):
    """
    Generates PNG files based on the uploaded SVG file after the model is saved.
    This process is asynchronous and non-blocking for the user.
    """
    sizes = settings.PNG_ICON_SIZES
    png_folder = settings.CITY_FURNITURE_DEVICE_TYPE_PNG_ICON_DESTINATION

    # This block ensures the signal only runs for newly created objects
    # that have an SVG file.
    if created and instance.file and instance.file.name.endswith(".svg"):
        try:
            with instance.file.open("rb") as svg_file:
                svg_bytestring = svg_file.read()
        except IOError as e:
            logger.error(f"Unable to read {instance.file.name}: {e}")
            return

        for size in sizes:
            svg_file_name = os.path.basename(instance.file.name)
            png_file_name = svg_file_name.replace(".svg", ".png")
            png_file_path = os.path.join(png_folder, str(size), png_file_name)

            try:
                png_data = cairosvg.svg2png(bytestring=svg_bytestring, output_width=size, output_height=size)
            except Exception as e:
                logger.error(f"Unable to convert {png_file_name} to PNG: {e}")
                return
            try:
                png_file_content = ContentFile(png_data)
                default_storage.save(png_file_path, png_file_content)
            except Exception as e:
                logger.error(f"Unable to store {png_file_path}: {e}")
                return

            logger.info(f"PNG icon generated: {png_file_path}")
