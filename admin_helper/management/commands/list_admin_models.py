from collections import defaultdict

from django.apps import apps
from django.contrib import admin
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Lists all registered Django Admin models and their Admin class paths"

    def handle(self, *_args, **_options):
        # Ensure all models are loaded before checking the registry
        apps.get_models()

        registry = admin.site._registry

        if not registry:
            self.stderr.write(self.style.WARNING("No models are registered with the admin site."))
            return

        # Group the registry data by App for cleaner output
        app_dict = defaultdict(list)
        for model, admin_instance in registry.items():
            app_label = model._meta.app_label
            admin_class = admin_instance.__class__
            admin_path = f"{admin_class.__module__}.{admin_class.__name__}"
            model_name = model._meta.object_name

            # Look for Inlines attached to this Admin
            inlines_list = []
            for inline_class in admin_instance.inlines:
                inline_path = f"{inline_class.__module__}.{inline_class.__name__}"
                inline_model = inline_class.model._meta.object_name
                inlines_list.append((inline_model, inline_path))

            app_dict[app_label].append((model_name, admin_path, inlines_list))

        self.stdout.write(self.style.SUCCESS(f"Found {len(registry)} registered admin models:\n"))

        # Print the grouped data
        for app_label, models in sorted(app_dict.items()):
            self.stdout.write(self.style.SUCCESS(f"App: {app_label}"))
            self.stdout.write("-" * 40)

            for model_name, admin_path, inlines in sorted(models):
                self.stdout.write(f"  Model: {model_name}")
                self.stdout.write(f"  Admin: {admin_path}")

                if inlines:
                    self.stdout.write(self.style.WARNING("  Inlines:"))
                    for inline_model, inline_path in inlines:
                        self.stdout.write(f"      Model: {inline_model}")
                        self.stdout.write(f"      Admin: {inline_path}")
                        self.stdout.write("\n")

                self.stdout.write("\n")
