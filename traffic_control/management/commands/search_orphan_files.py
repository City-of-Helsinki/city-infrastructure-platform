import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from django.apps import apps
from django.conf import settings
from django.core.files.storage import storages
from django.db.models import FileField

from cityinfra.storages.backends.non_leaky_azure_storage import NonLeakyAzureStorage
from command_tracker.management.trackable_command import TrackableCommand


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
        self.default_storage: NonLeakyAzureStorage = storages["default"]
        self.icon_storage: NonLeakyAzureStorage = storages["icons"]

    def handle(self, *args, **options):
        self._log("Analyzing storages...")

        # Complex analysis steps
        default_analysis = self._analyze_default_attachments()
        icon_analysis = self._analyze_icon_storage()

        # Simple analysis step
        odd_files = (default_analysis.all_files | icon_analysis.all_files) - (
            default_analysis.recognized_files | icon_analysis.recognized_files
        )
        self._report_flat_list(
            "Odd files (location doesn't match any expected file path, may occur if a model's file field is removed "
            "or has its upload_to path altered, for example).",
            odd_files,
        )

    def _log(self, message: str, style=None):
        """Add message to execution log and output to STDOUT, potentially styled."""
        self.stdout.write(message, style_func=style)
        self.execution_log.append(message)

    def _analyze_default_attachments(self) -> StorageAnalysis:
        # Scan storage for files
        default_storage_files: set[str] = set(self.default_storage.list_all())

        # Scan models for attachment references
        db_attachment_reference_map: dict[str, list[FileReference]] = defaultdict(list)
        attachment_expected_prefixes: set[str] = set()

        for model in apps.get_models():
            file_fields = [f for f in model._meta.get_fields() if isinstance(f, FileField)]
            for field in file_fields:
                if field.storage == self.icon_storage:
                    continue
                if field.storage != self.default_storage:
                    self._log(
                        f"WARNING: Model {model.__name__}.{field.name} uses an unrecognized storage.",
                        style=self.style.WARNING,
                    )
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
        self._report_flat_list(
            "Orphan attachments (exist in storage, but aren't referenced by database)", orphan_attachments
        )
        self._report_dangling_references(
            "Dangling attachment references (referenced by database, missing from storage)", dangling_attachment_map
        )

        return StorageAnalysis(all_files=default_storage_files, recognized_files=expected_attachments)

    def _get_db_svg_reference_map(self) -> dict[str, list[FileReference]]:
        """Scans models and returns a mapping of icon SVG filenames to their database references."""
        db_svg_reference_map: dict[str, list[FileReference]] = defaultdict(list)
        for model in apps.get_models():
            file_fields = [f for f in model._meta.get_fields() if isinstance(f, FileField)]
            for field in file_fields:
                if field.storage == self.icon_storage:
                    for db_entry in model.objects.all().only(field.name):
                        file_val = getattr(db_entry, field.name)
                        if file_val and file_val.name:
                            db_svg_reference_map[file_val.name].append(
                                FileReference(model_name=model.__name__, field_name=field.name, entry_pk=db_entry.pk)
                            )
        return db_svg_reference_map

    def _analyze_icon_storage(self) -> StorageAnalysis:
        # Scan storage for files
        icon_storage_files: set[str] = set(self.icon_storage.list_all())

        # Retrieve model icon references
        db_svg_reference_map = self._get_db_svg_reference_map()
        db_svg_references = set(db_svg_reference_map.keys())

        # Categorize storage files into SVG and PNGs
        svg_pattern = re.compile(r"^icons/(?P<model>.+)/svg/(?P<filename>.+)\.svg$")
        png_pattern = re.compile(r"^icons/(?P<model>.+)/png/(?P<size>\d+)/(?P<filename>.+)\.png$")

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

        # Map dangling icons to their specific database locations
        dangling_icon_map = {filename: db_svg_reference_map[filename] for filename in dangling_icons}

        # Report icon storage situation
        self._report_flat_list(
            "Orphan icons (icon SVG exists in storage, but isn't referenced by database)", orphan_icons
        )
        self._report_dangling_references(
            "Dangling icon references (SVG icon referenced by database, missing from storage)", dangling_icon_map
        )
        self._report_mapping_to_string(
            "Orphan PNGs (PNG icon exists in storage without a corresponding SVG file)",
            dangling_png_map,
            "expected SVG",
        )
        # Collapse the lists into comma-separated strings
        missing_pngs_by_svg = {svg: ", ".join(sizes) for svg, sizes in missing_pngs_by_svg_list.items()}
        self._report_mapping_to_string(
            "Missing PNGs (Valid SVG icon exists in storage but missing these PNG sizes)",
            missing_pngs_by_svg,
            "missing sizes",
        )

        return StorageAnalysis(
            all_files=icon_storage_files,
            recognized_files=db_svg_references | storage_svgs | storage_pngs,  # THIS IS BOTCHED, SHOULD BE (recognized_svg | recognized_pngs)
        )

    # Report utility functions
    def _report_flat_list(self, title: str, items: Iterable[str]) -> None:
        """Outputs a flat list of strings."""
        self._log(f"\n{title}")
        for item in sorted(items):
            self._log(f"    {item}")

    def _report_mapping_to_string(self, title: str, mapping: dict[str, str], value_label: str) -> None:
        """Outputs a list of strings, each appended with inline labeled metadata (a string)."""
        self._log(f"\n{title}")
        for key, value in sorted(mapping.items()):
            self._log(f"    {key} ({value_label}: {value})")

    def _report_dangling_references(self, title: str, mapping: dict[str, list[FileReference]]) -> None:
        """
        Outputs a list of missing filenames, detailing the DB models/fields/PKs that point to them.

        Dangling database references are exceptionally reported as a nested list because it is technically possible for
        multiple database rows to point to the same non-existent file, though most often we should expect to see a
        single dangling reference per file.
        """
        self._log(f"\n{title}")
        for filename, references in sorted(mapping.items()):
            self._log(f"    {filename}")
            for ref in references:
                self._log(f"        {ref.model_name}.{ref.field_name} (PK: {ref.entry_pk})")


def _get_file_field_prefix(field: FileField) -> str:
    """Return a FileField.upload_to field without trailing slash. e.g. 'path/to/upload/' -> 'path/to/upload'"""
    return field.upload_to.rstrip("/")


def _get_file_prefix(file: str) -> str:
    """Return the directory of a file without trailing slash. e.g. 'path/to/upload/file.ext" -> 'path/to/upload'"""
    return file.rsplit("/", 1)[0]
