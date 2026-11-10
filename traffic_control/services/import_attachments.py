"""Staging area for attachment files uploaded during an admin import.

The django-import-export admin import is a two step process: first the uploaded data file is
processed in a dry run, after which the user confirms the import in a second request. Files that
were uploaded in the first request are no longer available in the second one, so attachment files
need to be staged in persistent storage in between.

The staging area uses Django's default storage (which is an Azure Blob container in deployed
environments) instead of a local temporary directory, because consecutive requests are not
guaranteed to be handled by the same process or host.
"""

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.core.files.storage import default_storage, Storage
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from traffic_control.services.virus_scan import (
    add_virus_scan_errors_to_auditlog,
    clam_av_scan,
    get_error_details_message,
)
from traffic_control.utils import get_illegal_file_types

logger = logging.getLogger(__name__)

STAGING_ROOT = "import_attachments"


class AttachmentStagingError(Exception):
    """Raised when uploaded attachment files cannot be staged."""


@dataclass
class BatchDiscardResult:
    """Outcome of discarding a single staged attachment batch.

    Attributes:
        deleted (List[str]): Names of the files that were deleted.
        failed (List[str]): Names of the files that could not be deleted.
    """

    deleted: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)


def get_staging_storage() -> Storage:
    """Return the storage used for staging attachment files.

    Returns:
        Storage: Django's default file storage.
    """
    return default_storage


def sanitize_filename(filename: str) -> str:
    """Return the bare, path-free name of an uploaded file.

    Args:
        filename (str): Name as given by the uploading client.

    Returns:
        str: Filename without any directory components.

    Raises:
        AttachmentStagingError: If the name is empty or resolves to a directory traversal.
    """
    name = os.path.basename((filename or "").strip().replace("\\", "/"))
    if not name or name in (".", ".."):
        raise AttachmentStagingError(f"Invalid attachment file name: '{filename}'")
    return name


def get_batch_prefix(batch_id: str) -> str:
    """Return the storage prefix holding a staged batch.

    Args:
        batch_id (str): Identifier of the staged batch.

    Returns:
        str: Storage directory path of the batch.
    """
    return f"{STAGING_ROOT}/{_validate_batch_id(batch_id)}"


def stage_files(files: Iterable[File]) -> Optional[str]:
    """Store uploaded attachment files into the staging area.

    Args:
        files (Iterable[File]): Uploaded files to stage.

    Returns:
        Optional[str]: Identifier of the created batch, or ``None`` when no files were given.

    Raises:
        AttachmentStagingError: If two uploaded files share the same name.
    """
    files = [f for f in files if f is not None]
    if not files:
        return None

    batch_id = str(uuid.uuid4())
    storage = get_staging_storage()
    seen: Dict[str, str] = {}

    for uploaded_file in files:
        name = sanitize_filename(uploaded_file.name)
        if name in seen:
            discard_batch(batch_id)
            raise AttachmentStagingError(f"Duplicate attachment file name in upload: '{name}'")

        uploaded_file.seek(0)
        seen[name] = storage.save(f"{get_batch_prefix(batch_id)}/{name}", uploaded_file)

    logger.info("Staged %s attachment file(s) as import batch %s", len(seen), batch_id)
    return batch_id


def _listdir(path: str) -> Tuple[List[str], List[str]]:
    """List the directories and files under a path of the staging storage.

    The path is always normalized to end with a slash: ``AzureStorage.listdir`` strips the given
    path as a plain prefix, so without the trailing slash every blob is misclassified as a
    directory named ``""`` and no files are returned at all.

    Args:
        path (str): Storage path to list.

    Returns:
        Tuple[List[str], List[str]]: Directory names and file names, both empty when the path
            does not exist.
    """
    prefix = path if path.endswith("/") else f"{path}/"
    try:
        directories, filenames = get_staging_storage().listdir(prefix)
    except (FileNotFoundError, NotADirectoryError):
        return [], []

    return [name for name in directories if name], [name for name in filenames if name]


def list_staged(batch_id: Optional[str]) -> Dict[str, str]:
    """List the files staged in a batch.

    Args:
        batch_id (Optional[str]): Identifier of the staged batch.

    Returns:
        Dict[str, str]: Mapping of original file name to its path in the staging storage.
    """
    if not batch_id:
        return {}

    prefix = get_batch_prefix(batch_id)
    _, filenames = _listdir(prefix)

    return {name: f"{prefix}/{name}" for name in filenames}


def open_staged(batch_id: str, filename: str) -> File:
    """Open a single staged attachment file.

    Args:
        batch_id (str): Identifier of the staged batch.
        filename (str): Name of the file inside the batch.

    Returns:
        File: Opened file object.

    Raises:
        AttachmentStagingError: If the file is not part of the batch.
    """
    staged = list_staged(batch_id)
    name = sanitize_filename(filename)
    if name not in staged:
        raise AttachmentStagingError(f"Attachment file '{name}' is not part of import batch {batch_id}")

    return get_staging_storage().open(staged[name], "rb")


def discard_batch(batch_id: Optional[str]) -> BatchDiscardResult:
    """Delete every file of a staged batch and the batch directory itself.

    File deletion errors are logged and collected instead of raised, so that a single unremovable
    file does not prevent the rest of the batch from being deleted.

    Args:
        batch_id (Optional[str]): Identifier of the staged batch.

    Returns:
        BatchDiscardResult: Names of the deleted files and of the files that could not be deleted.
    """
    if not batch_id:
        return BatchDiscardResult()

    storage = get_staging_storage()
    result = BatchDiscardResult()
    for name, path in list_staged(batch_id).items():
        try:
            storage.delete(path)
        except OSError:
            logger.warning("Could not delete staged attachment file %s", path, exc_info=True)
            result.failed.append(name)
        else:
            result.deleted.append(name)

    _remove_batch_directory(batch_id)
    logger.info("Discarded import attachment batch %s", batch_id)
    return result


def _remove_batch_directory(batch_id: str) -> None:
    """Remove the emptied batch directory from a directory based storage.

    Storages that have no real directories, such as Azure Blob storage, do not leave anything
    behind when the files are deleted, so nothing needs to be done for them.

    Args:
        batch_id (str): Identifier of the staged batch.

    Returns:
        None
    """
    storage = get_staging_storage()
    try:
        directory = storage.path(get_batch_prefix(batch_id))
    except (NotImplementedError, AttributeError):
        return

    try:
        os.rmdir(directory)
    except OSError:
        logger.debug("Could not remove staged attachment batch directory %s", directory, exc_info=True)


def list_batch_ids() -> List[str]:
    """List the identifiers of all currently staged batches.

    Returns:
        List[str]: Batch identifiers found in the staging area.
    """
    directories, _ = _listdir(STAGING_ROOT)
    return directories


def list_stale_batches(max_age: timedelta) -> List[str]:
    """List staged batches that are older than the given age.

    Args:
        max_age (timedelta): Maximum age a staged batch may have.

    Returns:
        List[str]: Identifiers of the stale batches.
    """
    cutoff = timezone.now() - max_age
    stale = []

    for batch_id in list_batch_ids():
        modified_at = _get_batch_modified_time(batch_id)
        if modified_at is not None and modified_at > cutoff:
            continue
        stale.append(batch_id)

    return stale


def _get_batch_modified_time(batch_id: str):
    """Return the most recent modification time of a batch's files.

    Args:
        batch_id (str): Identifier of the staged batch.

    Returns:
        Optional[datetime]: Latest modification time, or ``None`` if it cannot be determined.
    """
    storage = get_staging_storage()
    times = []
    for path in list_staged(batch_id).values():
        try:
            times.append(storage.get_modified_time(path))
        except (NotImplementedError, OSError):
            continue
    return max(times) if times else None


def _validate_batch_id(batch_id: str) -> str:
    """Validate that a batch identifier is a UUID.

    Args:
        batch_id (str): Identifier to validate.

    Returns:
        str: The validated identifier.

    Raises:
        AttachmentStagingError: If the identifier is not a valid UUID.
    """
    try:
        return str(uuid.UUID(str(batch_id)))
    except (ValueError, AttributeError, TypeError):
        raise AttachmentStagingError(f"Invalid import attachment batch id: '{batch_id}'")


def stage_import_attachments(uploaded_files: Sequence[File], user: Any = None, model: Any = None) -> Optional[str]:
    """Virus scan and stage attachment files uploaded on the admin import page.

    Args:
        uploaded_files (Sequence[File]): Files uploaded with the import form.
        user (Any): User performing the import, used for audit logging.
        model (Any): Model being imported, used for audit logging.

    Returns:
        Optional[str]: Identifier of the staged batch, or ``None`` if no files were uploaded.

    Raises:
        ValidationError: If a file has an illegal type or does not pass the virus scan.
    """
    uploaded_files = [f for f in uploaded_files or [] if f is not None]
    if not uploaded_files:
        return None

    illegal_file_types = get_illegal_file_types([f.name for f in uploaded_files])
    if illegal_file_types:
        raise ValidationError(_("Illegal file types: %(types)s") % {"types": ", ".join(sorted(illegal_file_types))})

    virus_scan_errors = clam_av_scan([("FILES", f) for f in uploaded_files])["errors"]
    if virus_scan_errors:
        if model is not None:
            add_virus_scan_errors_to_auditlog(virus_scan_errors, user, model, object_id=None)
        raise ValidationError(
            _("Virus scan failure: %(details)s") % {"details": get_error_details_message(virus_scan_errors)}
        )

    try:
        return stage_files(uploaded_files)
    except AttachmentStagingError as error:
        raise ValidationError(str(error))
