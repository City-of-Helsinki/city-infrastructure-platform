"""Print a sanitized SQL dump of the database to stdout.

Usage:
    oc exec <api-pod> -- bash -o pipefail -c './manage.py dump_sanitized_db | gzip' > sanitized_db.sql.gz

Restore into an empty database:
    docker compose exec -T db dropdb -U city-infrastructure-platform --force --if-exists city-infrastructure-platform
    docker compose exec -T db createdb -U city-infrastructure-platform city-infrastructure-platform
    gunzip -c sanitized_db.sql.gz | docker compose exec -T db \
        psql -U city-infrastructure-platform -v ON_ERROR_STOP=1 -q -o /dev/null city-infrastructure-platform

After restoring:
- All passwords and OIDC logins are unusable. Create a user with ``createsuperuser``.
- Run ``migrate`` if your branch is ahead of the dumped environment.

Uploaded files are not part of the dump.
"""

from typing import Any

from django.core.management.base import CommandError

from command_tracker.management.trackable_command import TrackableCommand
from traffic_control.services.sanitized_db_dump import SanitizedDumpError, write_sanitized_dump


class Command(TrackableCommand):
    help = "Print a SQL dump of the database to stdout, with personal data replaced or left out."

    def handle(self, *args: Any, **options: Any) -> None:
        """Write the sanitized dump to stdout.

        Args:
            *args (Any): Positional arguments (unused).
            **options (Any): Parsed command options (unused).

        Returns:
            None

        Raises:
            CommandError: If the dump could not be made.
        """
        try:
            write_sanitized_dump(self.stdout.buffer)
        except SanitizedDumpError as error:
            raise CommandError(str(error)) from error
