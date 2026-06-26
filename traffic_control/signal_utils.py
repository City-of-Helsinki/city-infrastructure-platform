import logging
import os
from typing import Any, Optional

import cairosvg
from auditlog.models import LogEntry
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models.signals import post_delete, post_save, pre_save

logger = logging.getLogger("django")

# Sentinel used to distinguish "attribute not set" from an explicitly stored None.
_DB_VALUE_UNSET = object()
# Key for tracking which `_loaded_*_id` attributes have been patched onto a model's from_db.
_PATCHED_FROM_DB_ATTRS_KEY = "_signal_utils_patched_from_db_attrs"


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
                logger.error("Unable to convert %s to PNG: %s", png_file_name, e)
                return
            try:
                png_file_content = ContentFile(png_data)
                instance.file.storage.save(png_file_path, png_file_content)
            except Exception as e:
                logger.error("Unable to store %s: %s", png_file_path, e)
                return

            logger.debug("PNG icon generated: %s", png_file_path)


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
                        logger.debug("PNG file deleted: %s", png_file_path)
                    except Exception as e:
                        logger.error("Unable to delete %s: %s", png_file_path, e)

            # Delete the main SVG file
            instance.file.storage.delete(instance.file.name)
            logger.debug("SVG file deleted: %s", instance.file.name)

    except Exception as e:
        logger.error("Error deleting files for instance %s: %s", instance.pk, e)


def _create_parent_log_entry(parent, message, action=None):
    """Helper to create an audit log entry for a parent model."""
    if action is None:
        action = LogEntry.Action.UPDATE

    changes = {"relations": [message, None]} if "removed" in message else {"relations": [None, message]}
    if "updated" in message:
        changes = {"relations": [message, message]}

    try:
        LogEntry.objects.log_create(
            instance=parent,
            action=action,
            changes=changes,
        )
        logger.debug("Successfully created log entry for %s: %s", parent, message)
    except Exception as e:
        logger.error("Failed to create log entry for %s: %s", parent, e, exc_info=True)


def _extend_model_from_db(model: type, loaded_attr: str, source_id_attr: str) -> None:
    """Patch model.from_db to cache a FK id on every loaded instance.

    This allows signal handlers to read the pre-modification FK id without
    issuing an extra database query in pre_save.  Calling this function more
    than once for the same (model, loaded_attr) pair is safe and a no-op.

    Args:
        model (type): The Django model class to patch.
        loaded_attr (str): Attribute name to store the cached id (e.g. ``_loaded_parent_id``).
        source_id_attr (str): FK id attribute name to cache (e.g. ``parent_id``).
    """
    already_patched: frozenset[str] = getattr(model, _PATCHED_FROM_DB_ATTRS_KEY, frozenset())
    if loaded_attr in already_patched:
        return

    original_from_db = model.from_db

    @classmethod  # type: ignore[misc]
    def patched_from_db(cls, db: str, field_names: list, values: list) -> Any:
        instance = original_from_db.__func__(cls, db, field_names, values)
        setattr(instance, loaded_attr, instance.__dict__.get(source_id_attr))
        return instance

    model.from_db = patched_from_db
    setattr(model, _PATCHED_FROM_DB_ATTRS_KEY, already_patched | {loaded_attr})


def _fetch_parent_by_id(sender: type, parent_field_name: str, parent_id: Any, using: str) -> Optional[Any]:
    """Fetch the parent model instance for the given pk.

    Args:
        sender (type): The child model class, used to resolve the parent model.
        parent_field_name (str): The FK field name on the child model.
        parent_id (Any): Primary key of the parent to fetch, or None.
        using (str): Database alias to use.

    Returns:
        Optional[Any]: The parent model instance, or None if parent_id is None.
    """
    if parent_id is None:
        return None
    parent_model = sender._meta.get_field(parent_field_name).related_model
    try:
        return parent_model._default_manager.using(using).get(pk=parent_id)
    except parent_model.DoesNotExist:
        return None


def _get_old_parent(
    sender: type,
    instance: Any,
    parent_field_name: str,
    loaded_parent_id_attr: str,
    using: str,
) -> Optional[Any]:
    """Return the old parent value without a DB query when the parent has not changed.

    Falls back to a database query when the cached id is absent or when the parent
    FK has actually changed (and we need the old parent object for audit logging).

    Args:
        sender (type): The child model class.
        instance (Any): The child model instance about to be saved.
        parent_field_name (str): The FK field name pointing to the parent.
        loaded_parent_id_attr (str): Instance attribute holding the cached parent id.
        using (str): Database alias.

    Returns:
        Optional[Any]: The parent model instance before the pending save, or None.
    """
    loaded_parent_id = getattr(instance, loaded_parent_id_attr, _DB_VALUE_UNSET)
    if loaded_parent_id is _DB_VALUE_UNSET:
        return _fetch_old_parent_value(sender, instance, parent_field_name, using)
    if loaded_parent_id == getattr(instance, f"{parent_field_name}_id", None):
        return getattr(instance, parent_field_name, None)
    return _fetch_parent_by_id(sender, parent_field_name, loaded_parent_id, using)


def _fetch_old_parent_value(sender, instance, parent_field_name, using):
    """Helper to fetch the old parent value from the database."""
    try:
        db_instance = sender._default_manager.using(using).only("pk", parent_field_name).get(pk=instance.pk)
        return getattr(db_instance, parent_field_name)
    except sender.DoesNotExist:
        logger.warning("Could not find %s pk=%s in database during pre_save", sender.__name__, instance.pk)
        return None


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
    loaded_parent_id_attr = f"_loaded_{parent_field_name}_id"

    # Patch from_db to cache the parent FK id at load time, eliminating the N+1
    # query in cache_old_parent when the parent has not changed.
    _extend_model_from_db(child_model, loaded_parent_id_attr, f"{parent_field_name}_id")

    def cache_old_parent(sender, instance, **kwargs):
        # Only cache if this is an update (instance has pk and exists in DB)
        if instance.pk and not instance._state.adding:
            using = kwargs.get("using") or instance._state.db or "default"
            old_parent_value = _get_old_parent(sender, instance, parent_field_name, loaded_parent_id_attr, using)
            setattr(instance, cache_attr, old_parent_value)
            if old_parent_value:
                logger.debug(
                    "Cached old %s for %s pk=%s: %s", parent_field_name, sender.__name__, instance.pk, old_parent_value
                )
        else:
            # New instance, no old parent
            setattr(instance, cache_attr, None)

    def log_parent_change(sender, instance, created, **kwargs):
        old_parent = getattr(instance, cache_attr, None)
        new_parent = getattr(instance, parent_field_name)

        logger.debug(
            "log_parent_change for %s pk=%s: created=%s, old_parent=%s, new_parent=%s",
            sender.__name__,
            instance.pk,
            created,
            old_parent,
            new_parent,
        )

        # Log removal from the old parent if the parent has changed
        if not created and old_parent and old_parent != new_parent:
            message = f"{child_model_name} '{instance}' was removed."
            logger.debug("Creating removal log entry: %s for %s", message, old_parent)
            _create_parent_log_entry(old_parent, message)

        # Log addition or update to the new parent
        if new_parent:
            is_new_relation = created or old_parent != new_parent
            message = (
                f"{child_model_name} '{instance}' was added."
                if is_new_relation
                else f"{child_model_name} '{instance}' was updated."
            )
            logger.debug("Creating log entry for parent %s: %s", new_parent, message)
            _create_parent_log_entry(new_parent, message)

    def log_parent_deletion(sender, instance, **kwargs):
        """Log when a child is deleted from its parent."""
        parent = getattr(instance, parent_field_name, None)

        if parent:
            message = f"{child_model_name} '{instance}' was removed."
            logger.debug("Creating deletion log entry: %s for %s", message, parent)
            _create_parent_log_entry(parent, message)

    pre_save.connect(
        cache_old_parent,
        sender=child_model,
        dispatch_uid=f"cache_old_parent_{child_model.__name__}_{parent_field_name}",
        weak=False,  # Don't use weak references for local functions
    )
    post_save.connect(
        log_parent_change,
        sender=child_model,
        dispatch_uid=f"log_parent_change_{child_model.__name__}_{parent_field_name}",
        weak=False,  # Don't use weak references for local functions
    )
    post_delete.connect(
        log_parent_deletion,
        sender=child_model,
        dispatch_uid=f"log_parent_deletion_{child_model.__name__}_{parent_field_name}",
        weak=False,  # Don't use weak references for local functions
    )
