import logging
import os

import cairosvg
from auditlog.models import LogEntry
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models.signals import post_save, pre_save

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


def create_auditlog_signals_for_parent_model(child_model, parent_field_name):
    """
    A factory that creates and connects pre_save and post_save signal handlers
    for a child model to audit log changes on its parent model.

    :param child_model: The child model class (e.g., AdditionalSignReal).
    :param parent_field_name: The name of the ForeignKey field on the child model
                              that points to the parent model (e.g., 'parent').
    """
    cache_attr = f"_old_{parent_field_name}"
    child_model_name = child_model._meta.verbose_name.capitalize()

    def cache_old_parent(sender, instance, **kwargs):
        if instance.pk:
            try:
                old_instance = sender.objects.get(pk=instance.pk)
                setattr(instance, cache_attr, getattr(old_instance, parent_field_name))
            except sender.DoesNotExist:
                setattr(instance, cache_attr, None)

    def log_parent_change(sender, instance, created, **kwargs):
        old_parent = getattr(instance, cache_attr, None)
        new_parent = getattr(instance, parent_field_name)

        # Log removal from the old parent if the parent has changed
        if not created and old_parent and old_parent != new_parent:
            message = f"{child_model_name} '{instance}' was removed."
            LogEntry.objects.log_create(
                instance=old_parent,
                action=LogEntry.Action.UPDATE,
                changes={"relations": [message, None]},
            )

        # Log addition or update to the new parent
        if new_parent:
            is_new_relation = created or old_parent != new_parent
            if is_new_relation:
                message = f"{child_model_name} '{instance}' was added."
                changes = {"relations": [None, message]}
            else:
                message = f"{child_model_name} '{instance}' was updated."
                changes = {"relations": [message, message]}

            LogEntry.objects.log_create(
                instance=new_parent,
                action=LogEntry.Action.UPDATE,
                changes=changes,
            )

    pre_save.connect(
        cache_old_parent,
        sender=child_model,
        dispatch_uid=f"cache_old_parent_{child_model.__name__}_{parent_field_name}",
    )
    post_save.connect(
        log_parent_change,
        sender=child_model,
        dispatch_uid=f"log_parent_change_{child_model.__name__}_{parent_field_name}",
    )
