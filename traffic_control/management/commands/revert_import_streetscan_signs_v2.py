import argparse
import json
from collections import defaultdict
from datetime import datetime
from typing import Literal

from auditlog.context import set_actor
from django.apps import apps
from django.core.management import BaseCommand, CommandParser
from django.db import transaction
from django.utils import timezone

from traffic_control.models import AdditionalSignReal, MountReal, SignpostReal, TrafficSignReal
from users.models import User
from users.utils import get_system_user

# Types
ModelAffectedByImport = AdditionalSignReal | MountReal | SignpostReal | TrafficSignReal
ActionType = Literal["create", "deactivate", "update"]

# Constants
BATCH_SIZE = 1000
REVERT_PHASES = (
    (AdditionalSignReal, "deactivate"),
    (AdditionalSignReal, "update"),
    (AdditionalSignReal, "create"),
    (SignpostReal, "deactivate"),
    (SignpostReal, "update"),
    (SignpostReal, "create"),
    (TrafficSignReal, "deactivate"),
    (TrafficSignReal, "update"),
    (TrafficSignReal, "create"),
    (MountReal, "deactivate"),
    (MountReal, "update"),
    (MountReal, "create"),
)
model_class_map = {model.__name__: model for model, _ in REVERT_PHASES}


class SplitStringsAction(argparse.Action):
    """Argparse Action to transform a "foo,bar,baz" argument into ["foo", "bar", "baz"]."""

    def __call__(self, parser, namespace, values, option_strings=None):
        setattr(namespace, self.dest, values.split(","))


class Command(BaseCommand):
    help = "Revert the effects of an import_streetscan_signs_v2 run"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--dry-run",
            help="Dry run",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "-f",
            "--file",
            help="Revert jsonl file produced by an import operation",
            required=True,
            metavar="FILE",
            dest="file_path",
            type=str,
        )
        parser.add_argument(
            "--ids",
            help="Filter UUIDs to be reverted, separated by comma. If omitted then any UUID may be reverted.",
            default=[],
            action=SplitStringsAction,
        )
        parser.add_argument(
            "--models",
            help=(
                "Models to be reverted, separated by comma. Default: "
                "AdditionalSignReal,MountReal,SignpostReal,TrafficSignReal"
            ),
            default=["AdditionalSignReal", "MountReal", "SignpostReal", "TrafficSignReal"],
            dest="model_names",
            action=SplitStringsAction,
        )
        parser.epilog = (
            "Note: When running a partial revert, the revert operation may bring more models or objects to the "
            "the operation. For example if a mount created by an import operation is removed, all objects that had "
            "their mount set to that object will be reverted as well. These side-effect reversals cascade to any "
            "dependent objects."
        )

    def handle(
        self,
        *,
        dry_run: bool,
        file_path: str,
        ids: list[str],
        model_names: list[str],
        **_kwargs: dict,
    ) -> None:
        timestamp = timezone.now()
        user = get_system_user()
        if dry_run:
            self.stdout.write("Running in --dry-run mode, all operations will be reverted at the end of the process")

        self.stdout.write(f"Models to revert: {', '.join(model_names)}")
        self.stdout.write(f"Object IDs to revert: {', '.join(ids) if ids else 'all'}")

        # [MODEL][ACTION_TYPE] -> [...ACTIONS]
        actions_by_model_and_action_type: dict[type[ModelAffectedByImport], dict[str, list]] = defaultdict(
            lambda: defaultdict(list)
        )
        # [MODEL][PK] -> UPDATE_ACTION
        update_by_model_and_pk: dict[type[ModelAffectedByImport], dict[str, dict[str, str]]] = defaultdict(
            lambda: defaultdict(dict)
        )

        with open(file_path, "rt") as file:
            for line in file:
                if line:
                    row = json.loads(line)
                    action_type = row["action"]
                    model = model_class_map.get(row["object_type"])
                    actions_by_model_and_action_type[model][action_type].append(row)
                    if action_type == "update":
                        pk = row["db_id"]
                        update_by_model_and_pk[model][pk] = row

        revert_models = [apps.get_model("traffic_control", model_name) for model_name in model_names]
        orphaned_pks_per_model: dict[type[ModelAffectedByImport], set[str]] = {
            AdditionalSignReal: set(),
            SignpostReal: set(),
            TrafficSignReal: set(),
        }
        with set_actor(user), transaction.atomic():
            # Phase A: Revert direct actions and collect orphaned objects
            for model, action_type in REVERT_PHASES:
                if model not in revert_models:
                    continue
                actions = actions_by_model_and_action_type[model][action_type]
                actions.reverse()
                self.stdout.write(f"Reverting {len(actions)} {action_type} operations for {model.__name__}...")
                new_orphaned_pks_per_model = self.reverse_actions(
                    model=model,
                    action_type=action_type,
                    actions=actions,
                    limit_to_pks=ids,
                    user=user,
                    timestamp=timestamp,
                )
                for key, values in new_orphaned_pks_per_model.items():
                    orphaned_pks_per_model[key].update(values)

            # Phase B: Process objects orphaned by reverted actions
            self.revert_updates_on_orphaned_objects(
                orphaned_pks_per_model=orphaned_pks_per_model,
                update_by_model_and_pk=update_by_model_and_pk,
                user=user,
                timestamp=timestamp,
            )

            if dry_run:
                self.stdout.write("Running in --dry-run mode, cancelling transaction.")
                transaction.set_rollback(True)

    def reverse_actions(
        self,
        *,
        model: ModelAffectedByImport,
        action_type: ActionType,
        actions: list[dict],
        limit_to_pks: list[str],
        user: User,
        timestamp: datetime,
    ) -> dict[type[ModelAffectedByImport], set[str]]:
        """Revert a set of actions on a model

        Returns: A map of primary key of orphaned object per model (in the case of "create" operations."""
        if len(actions) == 0:
            return {}

        if action_type == "create":
            if limit_to_pks:
                pks = {action["db_id"] for action in actions if action["db_id"] in limit_to_pks}
            else:
                pks = {action["db_id"] for action in actions}
            orphaned_pks_by_model = Command.detach_dependent_objects(model=model, pks=pks)
            deleted_qs = model.objects.filter(pk__in=pks)
            deleted_pks = {str(pk) for pk in deleted_qs.values_list("pk", flat=True)}
            deleted_qs.delete()
            missing_pks = pks - deleted_pks
            for pk in missing_pks:
                self.stdout.write(
                    self.style.WARNING(
                        f"{model.__name__} {pk} does not exist, unable to revert {action_type} operation"
                    )
                )
            return orphaned_pks_by_model

        entries = []
        if action_type in ["update", "deactivate"]:
            for action in actions:
                pk = action["db_id"]
                if limit_to_pks and pk not in limit_to_pks:
                    continue
                try:
                    entry = model.objects.get(pk=pk)
                    self.revert_update(entry=entry, row=action, timestamp=timestamp, user=user)
                    entries.append(entry)
                except model.DoesNotExist:
                    pk = action["db_id"]
                    self.stdout.write(
                        self.style.WARNING(
                            f"{model.__name__} {pk} does not exist, unable to revert {action_type} operation"
                        )
                    )
                    continue
        fields = set(actions[0]["old"]) | {"updated_by", "updated_at"}
        model.objects.bulk_update(entries, fields, BATCH_SIZE)
        return {}

    @staticmethod
    def revert_update(*, entry: ModelAffectedByImport, row: dict, timestamp: datetime, user: User) -> None:
        """Restores previous field values and updates audit metadata."""
        for field, value in row["old"].items():
            setattr(entry, field, value)
        entry.updated_by = user
        entry.updated_at = timestamp

    @staticmethod
    def detach_dependent_objects(
        *, model: ModelAffectedByImport, pks: set[str]
    ) -> dict[type[ModelAffectedByImport], set[str]]:
        """Clear assignments to the given items in the model before deletion.

        Returns: Sets of dependent objects by model that need to have their update operations reverted."""
        additional_sign_pks = set()
        signpost_pks = set()
        traffic_sign_pks = set()

        if model == MountReal:
            additional_qs = AdditionalSignReal.objects.filter(mount_real__pk__in=pks)
            signpost_qs = SignpostReal.objects.filter(mount_real__pk__in=pks)
            traffic_qs = TrafficSignReal.objects.filter(mount_real__pk__in=pks)

            additional_sign_pks = set(additional_qs.values_list("pk", flat=True))
            signpost_pks = set(signpost_qs.values_list("pk", flat=True))
            traffic_sign_pks = set(traffic_qs.values_list("pk", flat=True))

            additional_qs.update(mount_real=None)
            signpost_qs.update(mount_real=None)
            traffic_qs.update(mount_real=None)

        elif model == SignpostReal:
            additional_qs = AdditionalSignReal.objects.filter(signpost_real__pk__in=pks)
            signpost_qs = SignpostReal.objects.filter(parent__pk__in=pks)

            additional_sign_pks = set(additional_qs.values_list("pk", flat=True))
            signpost_pks = set(signpost_qs.values_list("pk", flat=True))

            additional_qs.update(signpost_real=None)
            signpost_qs.update(parent=None)

        elif model == TrafficSignReal:
            additional_qs = AdditionalSignReal.objects.filter(parent__pk__in=pks)

            additional_sign_pks = set(additional_qs.values_list("pk", flat=True))

            additional_qs.update(parent=None)

        return {
            AdditionalSignReal: {str(pk) for pk in additional_sign_pks},
            SignpostReal: {str(pk) for pk in signpost_pks},
            TrafficSignReal: {str(pk) for pk in traffic_sign_pks},
        }

    def revert_updates_on_orphaned_objects(
        self,
        orphaned_pks_per_model: dict[type[ModelAffectedByImport], set[str]],
        update_by_model_and_pk: dict[type[ModelAffectedByImport], dict[str, dict[str, str]]],
        user: User,
        timestamp: datetime,
    ) -> None:
        """Handles the final updates for secondary objects affected by reverted creates."""
        for model, pks in orphaned_pks_per_model.items():
            # We need to force a last update for secondary objects that have been affected by reverted create (left
            # operator of intersection) and have an available update operation to be reverted (right operator of
            # intersection)
            revertible_orphaned_pks = pks & set(update_by_model_and_pk[model])
            non_revertible_orphaned_pks = pks - revertible_orphaned_pks

            if non_revertible_orphaned_pks:
                sorted_pks = ", ".join(sorted(non_revertible_orphaned_pks))
                self.stdout.write(
                    f"{len(non_revertible_orphaned_pks)} secondary {model.__name__} objects orphaned by reverted "
                    f"CREATE operations do not have pending UPDATE operations and cannot be reverted: "
                    f"{sorted_pks}"
                )

            entries = model.objects.filter(
                pk__in=revertible_orphaned_pks,
                updated_at__lt=timestamp,  # Skip anything we have already updated during this revert operation
            )
            if len(entries) == 0:
                self.stdout.write(
                    f"No secondary {model.__name__} objects orphaned by reverted CREATE operations have pending "
                    "UPDATE operations to be reverted."
                )
                continue
            self.stdout.write(
                f"{len(entries)} secondary {model.__name__} objects orphaned by reverted CREATE operations have "
                "pending UPDATE operations to be reverted."
            )

            for entry in entries:
                row = update_by_model_and_pk[model][str(entry.pk)]
                self.revert_update(entry=entry, row=row, timestamp=timestamp, user=user)
            fields = set(update_by_model_and_pk[model][list(revertible_orphaned_pks)[0]]["old"]) | {
                "updated_by",
                "updated_at",
            }
            model.objects.bulk_update(entries, fields, BATCH_SIZE)
