"""
Base class for management commands that create dummy device types.
This reduces code duplication between traffic_control and city_furniture apps.
"""
from abc import ABC, abstractmethod

from django.core.management.base import BaseCommand
from django.db import transaction


class BaseCreateDummyDeviceTypeCommand(BaseCommand, ABC):
    """
    Abstract base class for creating dummy device types and assigning them
    to devices with device_type=None.
    """

    def add_arguments(self, parser):
        """Add common command-line arguments."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without making any changes",
        )
        parser.add_argument(
            "--models",
            nargs="+",
            choices=self.get_model_choices(),
            help="Specific models to update. If not provided, all models will be updated.",
        )
        parser.add_argument(
            "--list-ids",
            action="store_true",
            help="List the IDs of objects that have their device_type changed",
        )

    @abstractmethod
    def get_model_choices(self):
        """Return list of model name choices for the --models parameter."""
        pass

    @abstractmethod
    def get_all_models(self):
        """Return list of all models that have device_type field as (name, model_class) tuples."""
        pass

    @abstractmethod
    def get_or_create_dummy_device_type(self, dry_run):
        """
        Create or get the dummy device type.
        Should return the device type object or None if dry_run and created.
        """
        pass

    @abstractmethod
    def get_no_devices_message(self):
        """Return the message to display when no devices with device_type=None are found."""
        pass

    @abstractmethod
    def get_summary_message_prefix(self):
        """Return the prefix for the summary message (e.g., 'device', 'city furniture device')."""
        pass

    def filter_models(self, all_models, selected_models):
        """Filter models based on selection."""
        if selected_models:
            models_to_update = [(name, model) for name, model in all_models if name in selected_models]
            self.stdout.write(self.style.WARNING(f"Processing only selected models: {', '.join(selected_models)}"))
            return models_to_update
        return all_models

    def update_model(self, model_name, model, dummy_device_type, dry_run, list_ids):
        """Update a single model's objects with null device_type."""
        objects_with_null_device_type = model.objects.filter(device_type__isnull=True)

        ids_to_update = None
        if list_ids:
            ids_to_update = list(objects_with_null_device_type.values_list("id", flat=True))

        count = objects_with_null_device_type.count()

        if dry_run:
            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"Would update {count} {model_name} records with dummy device type")
                )
                if list_ids and ids_to_update:
                    self.stdout.write(
                        self.style.WARNING(f"  IDs that would be updated: {', '.join(map(str, ids_to_update))}")
                    )
            return count
        else:
            updated_count = objects_with_null_device_type.update(device_type=dummy_device_type)
            if updated_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"Updated {updated_count} {model_name} records with dummy device type")
                )
                if list_ids and ids_to_update:
                    self.stdout.write(self.style.WARNING(f"  Updated IDs: {', '.join(map(str, ids_to_update))}"))
            return updated_count

    def handle(self, *args, **options):
        """Main command handler."""
        dry_run = options["dry_run"]
        selected_models = options.get("models")
        list_ids = options["list_ids"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        with transaction.atomic():
            dummy_device_type = self.get_or_create_dummy_device_type(dry_run)

            all_models = self.get_all_models()
            models_to_update = self.filter_models(all_models, selected_models)

            total_updated = 0
            for model_name, model in models_to_update:
                total_updated += self.update_model(model_name, model, dummy_device_type, dry_run, list_ids)

            if total_updated == 0:
                self.stdout.write(self.style.WARNING(self.get_no_devices_message()))
            else:
                action = "Would update" if dry_run else "Updated"
                prefix = self.get_summary_message_prefix()
                self.stdout.write(
                    self.style.SUCCESS(f"Total: {action} {total_updated} {prefix} records with dummy device type")
                )

            if dry_run:
                # Rollback all changes in dry-run mode
                transaction.set_rollback(True)
