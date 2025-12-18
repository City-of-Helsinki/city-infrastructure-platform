from django.apps import apps
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Lists all models registered in the specified app."

    def add_arguments(self, parser):
        parser.add_argument("app_label", type=str, help="The name of the app (e.g., auth, admin)")

    def handle(self, *args, **options):
        app_label = options["app_label"]

        try:
            # 1. Get the AppConfig
            app_config = apps.get_app_config(app_label)
        except LookupError:
            raise CommandError(f"App '{app_label}' could not be found. Is it in INSTALLED_APPS?")

        # 2. Get the models
        models = app_config.get_models()

        self.stdout.write(self.style.MIGRATE_HEADING(f"Models in app '{app_label}':"))

        # 3. List them
        model_count = 0
        for model in models:
            model_count += 1
            model_name = model.__name__
            db_table = model._meta.db_table

            # formatting: ModelName (database_table_name)
            self.stdout.write(f"- {self.style.SUCCESS(model_name)} ({db_table})")

        if model_count == 0:
            self.stdout.write(self.style.WARNING("  No models found in this app."))
