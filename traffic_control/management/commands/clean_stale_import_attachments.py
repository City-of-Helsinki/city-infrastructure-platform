"""Management command for removing abandoned import attachment batches from the staging area."""

from datetime import timedelta
from typing import Any, Dict, List, Tuple

from django.core.management.base import CommandParser
from django.utils import timezone

from command_tracker.management.trackable_command import TrackableCommand
from traffic_control.enums import ImportAttachmentCleanupStatus
from traffic_control.models import ImportAttachmentCleanupRun
from traffic_control.services.import_attachments import discard_batch, list_staged, list_stale_batches
from users.utils import get_system_user

DEFAULT_MAX_AGE_HOURS = 24


class Command(TrackableCommand):
    help = (
        "Delete attachment files that were staged for an admin import but never used, for example because the "
        "import was abandoned after the preview step."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """Register the command's arguments.

        Args:
            parser (CommandParser): Parser to register the arguments on.

        Returns:
            None
        """
        parser.add_argument(
            "--max-age-hours",
            type=int,
            default=DEFAULT_MAX_AGE_HOURS,
            help=f"Delete staged batches older than this many hours. Defaults to {DEFAULT_MAX_AGE_HOURS}.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report the stale batches that would be deleted, without deleting anything.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Discard staged attachment batches older than the given age.

        Args:
            *args (Any): Positional arguments.
            **options (Any): Parsed command options.

        Returns:
            None

        Raises:
            Exception: Re-raises any fatal error hit while discarding, after recording the batches
                that were already discarded on the run.
        """
        max_age_hours = options["max_age_hours"]
        dry_run = options["dry_run"]

        cleanup_run = ImportAttachmentCleanupRun.objects.create(
            executed_by=get_system_user(),
            dry_run=dry_run,
            max_age_hours=max_age_hours,
        )
        self.stdout.write(f"Created import attachment cleanup run record: {cleanup_run.id}")

        discarded: Dict[str, List[str]] = {}
        failures: Dict[str, str] = {}

        try:
            self._discard_stale_batches(timedelta(hours=max_age_hours), dry_run, discarded, failures)
        except Exception as error:
            failures[""] = str(error)
            self._complete_run(cleanup_run, discarded, failures)
            raise

        self._complete_run(cleanup_run, discarded, failures)
        self._report(discarded, failures, dry_run)

    def _discard_stale_batches(
        self,
        max_age: timedelta,
        dry_run: bool,
        discarded: Dict[str, List[str]],
        failures: Dict[str, str],
    ) -> None:
        """Discard the stale batches, collecting the discarded file names and the failures.

        Failing to discard a single batch does not stop the cleanup: the failure is recorded and the
        remaining batches are still processed. The results are collected into the caller's
        dictionaries so that they survive a fatal error.

        Args:
            max_age (timedelta): Maximum age a staged batch may have.
            dry_run (bool): When ``True``, nothing is deleted.
            discarded (Dict[str, List[str]]): Mapping of batch id to the discarded file names, updated
                in place.
            failures (Dict[str, str]): Mapping of batch id to an error message, updated in place.

        Returns:
            None
        """
        for batch_id in list_stale_batches(max_age):
            try:
                self._discard_batch(batch_id, dry_run, discarded, failures)
            except Exception as error:
                failures[batch_id] = str(error)

    def _discard_batch(
        self,
        batch_id: str,
        dry_run: bool,
        discarded: Dict[str, List[str]],
        failures: Dict[str, str],
    ) -> None:
        """Discard a single stale batch and record its outcome.

        A batch whose directory was already empty is recorded as discarded with no files, because the
        batch itself was still cleaned up.

        Args:
            batch_id (str): Identifier of the staged batch.
            dry_run (bool): When ``True``, nothing is deleted.
            discarded (Dict[str, List[str]]): Mapping of batch id to the discarded file names, updated
                in place.
            failures (Dict[str, str]): Mapping of batch id to an error message, updated in place.

        Returns:
            None
        """
        if dry_run:
            discarded[batch_id] = sorted(list_staged(batch_id))
            return

        result = discard_batch(batch_id)
        if result.failed:
            failures[batch_id] = "Could not delete file(s): " + ", ".join(sorted(result.failed))
            if result.deleted:
                discarded[batch_id] = sorted(result.deleted)
            return

        discarded[batch_id] = sorted(result.deleted)

    def _complete_run(
        self,
        cleanup_run: ImportAttachmentCleanupRun,
        discarded: Dict[str, List[str]],
        failures: Dict[str, str],
    ) -> None:
        """Store the outcome of the cleanup on the run record.

        Args:
            cleanup_run (ImportAttachmentCleanupRun): Run record to update.
            discarded (Dict[str, List[str]]): Mapping of batch id to the discarded file names.
            failures (Dict[str, str]): Mapping of batch id to an error message.

        Returns:
            None
        """
        status, error_message = self._resolve_status(discarded, failures)
        cleanup_run.completed_at = timezone.now()
        cleanup_run.status = status
        cleanup_run.error_message = error_message
        cleanup_run.discarded_batches = discarded
        cleanup_run.discarded_batches_count = len(discarded)
        cleanup_run.files_discarded = sum(len(filenames) for filenames in discarded.values())
        cleanup_run.save()

    def _resolve_status(
        self,
        discarded: Dict[str, List[str]],
        failures: Dict[str, str],
    ) -> Tuple[str, str]:
        """Resolve the run status and error message from the collected results.

        Args:
            discarded (Dict[str, List[str]]): Mapping of batch id to the discarded file names.
            failures (Dict[str, str]): Mapping of batch id to an error message.

        Returns:
            Tuple[str, str]: Status value and the aggregated error message, which is empty on success.
        """
        if not failures:
            return ImportAttachmentCleanupStatus.SUCCESS, ""

        error_message = "\n".join(
            f"{batch_id}: {message}" if batch_id else message for batch_id, message in failures.items()
        )
        if discarded:
            return ImportAttachmentCleanupStatus.PARTIALLY_FAILED, error_message

        return ImportAttachmentCleanupStatus.FAILED, error_message

    def _report(self, discarded: Dict[str, List[str]], failures: Dict[str, str], dry_run: bool) -> None:
        """Write the cleanup result to stdout.

        Args:
            discarded (Dict[str, List[str]]): Mapping of batch id to the discarded file names.
            failures (Dict[str, str]): Mapping of batch id to an error message.
            dry_run (bool): Whether the cleanup was a dry run.

        Returns:
            None
        """
        for batch_id, message in failures.items():
            target = f"batch {batch_id}" if batch_id else "stale batches"
            self.stderr.write(self.style.ERROR(f"Failed to discard import attachment {target}: {message}"))

        if not discarded:
            self.stdout.write("No stale import attachment batches found.")
            return

        action = "Would discard" if dry_run else "Discarded"
        for batch_id, filenames in discarded.items():
            self._write_batch(action, batch_id, filenames)

        self.stdout.write(self.style.SUCCESS(f"{action} {len(discarded)} stale import attachment batch(es)."))

    def _write_batch(self, action: str, batch_id: str, filenames: List[str]) -> None:
        """Report a single batch and the files it contains.

        Args:
            action (str): Verb describing what is done to the batch.
            batch_id (str): Identifier of the staged batch.
            filenames (List[str]): Names of the files staged in the batch.

        Returns:
            None
        """
        file_count = len(filenames)
        self.stdout.write(f"{action} import attachment batch {batch_id} ({file_count} file(s))")
        for filename in filenames:
            self.stdout.write(f"  - {filename}")
