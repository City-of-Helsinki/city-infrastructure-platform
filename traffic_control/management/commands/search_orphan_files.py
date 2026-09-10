import posixpath
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from django.apps import apps
from django.conf import settings
from django.core.files.storage import Storage, storages
from django.db.models import FileField
from django.utils import timezone

from command_tracker.management.trackable_command import TrackableCommand
from traffic_control.models import SearchOrphanFilesRunInfo


@dataclass
class StorageAnalysis:
    all_files: set[str]
    recognized_files: set[str]


@dataclass
class FileReference:
    model_name: str
    field_name: str
    entry_pk: Any


class Command(TrackableCommand):
    help = (
        "Compares files in the storages with file references in the database and produces lists of discrepancies. "
        "Separates reports into attachments (AbstractFileModel), misc (other FileFields), and icons (SVG/PNG pairs)."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execution_log: list[str] = []

    def handle(self, *args, **options):
        start_timestamp = timezone.now()
        self._log("Analyzing storages...")

        # Complex analysis steps
        default_analysis = analyze_default_storage_utilization(log_function=self._log)
        icon_analysis = analyze_icon_storage_utilization(log_function=self._log)

        # Simple analysis step
        odd_files = (default_analysis.all_files | icon_analysis.all_files) - (
            default_analysis.recognized_files | icon_analysis.recognized_files
        )
        _report_flat_list(
            log_function=self._log,
            title=(
                "Odd files (location doesn't match any expected file path, may occur if a model's file field is"
                "removed or has its upload_to path altered, for example)."
            ),
            items=odd_files,
        )

        SearchOrphanFilesRunInfo.objects.create(
            started_at=start_timestamp,
            completed_at=timezone.now(),
            execution_log="\n".join(self.execution_log),
        )

    def _log(self, message: str, style=None) -> None:
        """Add message to execution log and output to STDOUT, potentially styled."""
        self.stdout.write(message, style_func=style)
        self.execution_log.append(message)


# Storage analysis


def analyze_default_storage_utilization(log_function: Callable = print) -> StorageAnalysis:
    # Scan storage for files
    default_storage_files: set[str] = set(_list_all_storage_files(storages["default"]))

    # Scan models for attachment references
    db_attachment_reference_map: dict[str, list[FileReference]] = defaultdict(list)
    attachment_expected_prefixes: set[str] = set()

    for model in apps.get_models():
        file_fields = [f for f in model._meta.get_fields() if isinstance(f, FileField)]
        for field in file_fields:
            # Skip icons, they're handled elsewhere
            if field.upload_to in [
                settings.TRAFFIC_CONTROL_DEVICE_TYPE_SVG_ICON_DESTINATION,
                settings.CITY_FURNITURE_DEVICE_TYPE_SVG_ICON_DESTINATION,
            ]:
                continue

            attachment_expected_prefixes.add(_get_file_field_prefix(field))
            for db_entry in model.objects.all().only(field.name):
                file_val = getattr(db_entry, field.name)
                if file_val and file_val.name:
                    db_attachment_reference_map[file_val.name].append(
                        FileReference(model_name=model.__name__, field_name=field.name, entry_pk=db_entry.pk)
                    )

    db_attachment_references = set(db_attachment_reference_map.keys())

    # Evaluate the relevant sets of expected, orphan, dangling attachments
    expected_attachments = {f for f in default_storage_files if _get_file_prefix(f) in attachment_expected_prefixes}
    orphan_attachments = expected_attachments - db_attachment_references
    dangling_attachments = db_attachment_references - default_storage_files

    # Map dangling references to their specific database locations
    dangling_attachment_map = {filename: db_attachment_reference_map[filename] for filename in dangling_attachments}

    # Report default storage situation
    _report_flat_list(
        log_function=log_function,
        title="Orphan attachments (exist in storage, but aren't referenced by database)",
        items=orphan_attachments,
    )
    _report_dangling_references(
        log_function=log_function,
        title="Dangling attachment references (referenced by database, missing from storage)",
        mapping=dangling_attachment_map,
    )

    return StorageAnalysis(all_files=default_storage_files, recognized_files=expected_attachments)


def _get_db_svg_reference_map() -> dict[str, list[FileReference]]:
    """Scans models and returns a mapping of icon SVG filenames to their database references."""
    db_svg_reference_map: dict[str, list[FileReference]] = defaultdict(list)
    for model in apps.get_models():
        file_fields = [f for f in model._meta.get_fields() if isinstance(f, FileField)]
        for field in file_fields:
            # Deal only with icons
            if field.upload_to not in [
                settings.TRAFFIC_CONTROL_DEVICE_TYPE_SVG_ICON_DESTINATION,
                settings.CITY_FURNITURE_DEVICE_TYPE_SVG_ICON_DESTINATION,
            ]:
                continue

            for db_entry in model.objects.all().only(field.name):
                file_val = getattr(db_entry, field.name)
                if file_val and file_val.name:
                    db_svg_reference_map[file_val.name].append(
                        FileReference(model_name=model.__name__, field_name=field.name, entry_pk=db_entry.pk)
                    )
    return db_svg_reference_map


def analyze_icon_storage_utilization(log_function: Callable = print) -> StorageAnalysis:
    # Scan storage for files
    icon_storage_files: set[str] = set(_list_all_storage_files(storages["icons"]))

    # Retrieve model icon references
    db_svg_reference_map = _get_db_svg_reference_map()
    db_svg_references = set(db_svg_reference_map.keys())

    # Categorize storage files into SVG and PNGs
    svg_pattern = re.compile(r"^icons/(?P<model>\w+)/svg/(?P<filename>[^/]+)\.svg$")
    png_pattern = re.compile(r"^icons/(?P<model>\w+)/png/(?P<size>\d+)/(?P<filename>[^/]+)\.png$")

    storage_svgs = set()
    storage_pngs = set()

    for filename in icon_storage_files:
        if svg_pattern.match(filename):
            storage_svgs.add(filename)
        elif png_pattern.match(filename):
            storage_pngs.add(filename)

    # Evaluate orphan, dangling, valid status of SVG references
    orphan_icons = storage_svgs - db_svg_references
    dangling_icons = db_svg_references - storage_svgs
    valid_svgs = storage_svgs & db_svg_references

    # Map dangling icon references to their specific database locations
    dangling_icon_map = {filename: db_svg_reference_map[filename] for filename in dangling_icons}

    # Evaluate missing PNG sizes for valid SVGs
    missing_pngs_by_svg_list = defaultdict(list)
    for svg_filename in valid_svgs:
        svg_match = svg_pattern.match(svg_filename)
        groups = svg_match.groupdict()
        for size in settings.PNG_ICON_SIZES:
            expected_png = f"icons/{groups['model']}/png/{size}/{groups['filename']}.png"
            if expected_png not in storage_pngs:
                missing_pngs_by_svg_list[svg_filename].append(str(size))

    # Find PNGs without matching SVG
    dangling_png_map: dict[str, str] = {}
    for png_filename in storage_pngs:
        png_match = png_pattern.match(png_filename)
        groups = png_match.groupdict()
        expected_svg = f"icons/{groups['model']}/svg/{groups['filename']}.svg"
        if expected_svg not in storage_svgs:
            dangling_png_map[png_filename] = expected_svg

    # Report icon storage situation
    _report_flat_list(
        log_function=log_function,
        title="Orphan icons (icon SVG exists in storage, but isn't referenced by database)",
        items=orphan_icons,
    )
    _report_dangling_references(
        log_function=log_function,
        title="Dangling icon references (SVG icon referenced by database, missing from storage)",
        mapping=dangling_icon_map,
    )
    _report_mapping_to_string(
        log_function=log_function,
        title="Orphan PNGs (PNG icon exists in storage without a corresponding SVG file)",
        value_label="expected SVG",
        mapping=dangling_png_map,
    )
    # Collapse the lists into comma-separated strings
    missing_pngs_by_svg = {svg: ", ".join(sizes) for svg, sizes in missing_pngs_by_svg_list.items()}
    _report_mapping_to_string(
        log_function=log_function,
        title="Missing PNGs (Valid SVG icon exists in storage but missing these PNG sizes)",
        value_label="missing sizes",
        mapping=missing_pngs_by_svg,
    )

    # We've already reported any details about SVG and PNG files in storage, so only files that aren't SVGs or PNGs
    # are treated as "unrecognized".
    return StorageAnalysis(all_files=icon_storage_files, recognized_files=storage_svgs | storage_pngs)


# Logging


def _report_flat_list(*, log_function: Callable, title: str, items: list[str] | set[str]) -> None:
    """Outputs a flat list of strings."""
    if len(items) == 0:
        return

    log_function(f"\n{title}")
    for item in sorted(items):
        log_function(f"    {item}")


def _report_mapping_to_string(*, log_function: Callable, title: str, mapping: dict[str, str], value_label: str) -> None:
    """Outputs a list of strings, each appended with inline labeled metadata (a string)."""
    if len(mapping) == 0:
        return

    log_function(f"\n{title}")
    for key, value in sorted(mapping.items()):
        log_function(f"    {key} ({value_label}: {value})")


def _report_dangling_references(*, log_function: Callable, title: str, mapping: dict[str, list[FileReference]]) -> None:
    """
    Outputs a list of missing filenames, detailing the DB models/fields/PKs that point to them.

    Dangling database references are exceptionally reported as a nested list because it is technically possible for
    multiple database rows to point to the same non-existent file, though most often we should expect to see a
    single dangling reference per file.
    """
    if len(mapping) == 0:
        return

    log_function(f"\n{title}")
    for filename, references in sorted(mapping.items()):
        log_function(f"    {filename}")
        for ref in references:
            log_function(f"        {ref.model_name}.{ref.field_name} (PK: {ref.entry_pk})")


# Path transformations


def _get_file_field_prefix(field: FileField) -> str:
    """Return a FileField.upload_to field without trailing slash. e.g. 'path/to/upload/' -> 'path/to/upload'"""
    return field.upload_to.rstrip("/")


def _get_file_prefix(file: str) -> str:
    """Return the directory of a file without trailing slash. e.g. 'path/to/upload/file.ext" -> 'path/to/upload'"""
    return file.rsplit("/", 1)[0]


# Listing all files in a storage


def _list_all_storage_files(storage: Storage) -> Iterable[str]:
    """
    Returns an iterable of all file paths in a Django storage.
    Uses native `.list_all()` if available (which is the case with our cloud storages), otherwise falls back to
    recursively walking the storage using Django's standard `.listdir()`.
    """
    # 1. Fast path: Use the list_all method if the storage provides it - provided by our cloud storages
    if hasattr(storage, "list_all") and callable(storage.list_all):
        return storage.list_all()

    # 2. Fallback: Recursively walk standard Django storages
    def _walk(path: str) -> list[str]:
        found_files = []
        try:
            directories, files = storage.listdir(path)
        except (NotImplementedError, FileNotFoundError, OSError):
            # Handle empty/missing directories or unsupported operations gracefully
            return []

        # Add files in the current directory
        for file in files:
            found_files.append(posixpath.join(path, file))

        # Recurse into subdirectories
        for directory in directories:
            found_files.extend(_walk(posixpath.join(path, directory)))

        return found_files

    return _walk("")
