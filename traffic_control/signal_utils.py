import logging
import os

import cairosvg
from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger("django")


def generate_pngs_on_svg_save(*, instance, png_folder):
    """
    Shared implementation of icon PNG file generation. Used by some custom post_save signal handlers in our code.
    """
    # This block ensures the signal only runs for objects that have an SVG file.
    if instance.file and instance.file.name.endswith(".svg"):
        try:
            with instance.file.open("rb") as svg_file:
                svg_bytestring = svg_file.read()
        except IOError as e:
            logger.error(f"Unable to read {instance.file.name}: {e}")
            return

        for size in settings.PNG_ICON_SIZES:
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
                instance.file.storage.save(png_file_path, png_file_content)
            except Exception as e:
                logger.error(f"Unable to store {png_file_path}: {e}")
                return

            logger.info(f"PNG icon generated: {png_file_path}")


def delete_icon_files_on_row_delete(*, instance, png_folder):
    """
    Deletes the SVG and associated PNG files from storage. Used by some custom post_save signal handlers in our code.
    """
    try:
        # Check if the file field is not empty before attempting to delete.
        if instance.file:
            # Delete all generated PNG files for different sizes
            svg_file_name = os.path.basename(instance.file.name)
            base_file_name = os.path.splitext(svg_file_name)[0]

            for size in settings.PNG_ICON_SIZES:
                png_file_path = os.path.join(png_folder, str(size), base_file_name + ".png")

                if instance.file.storage.exists(png_file_path):
                    try:
                        instance.file.storage.delete(png_file_path)
                        logger.info(f"PNG file deleted: {png_file_path}")
                    except Exception as e:
                        logger.error(f"Unable to delete {png_file_path}: {e}")

            # Delete the main SVG file
            instance.file.storage.delete(instance.file.name)
            logger.info(f"SVG file deleted: {instance.file.name}")

    except Exception as e:
        logger.error(f"Error deleting files for instance {instance.pk}: {e}")
