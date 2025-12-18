from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db.models.fields.reverse_related import ForeignObjectRel


class Command(BaseCommand):
    help = "Lists all incoming and outgoing relationships for a given model with strict table alignment."

    def add_arguments(self, parser):
        parser.add_argument("app_label", type=str, help="App label (e.g. auth)")
        parser.add_argument("model_name", type=str, help="Model name (e.g. User)")

    def handle(self, *args, **options):
        app_label = options["app_label"]
        model_name = options["model_name"]

        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            raise CommandError(f"Model '{model_name}' not found in app '{app_label}'.")

        # 1. Collect Data First (don't print yet)
        outgoing_rows = []
        incoming_rows = []

        # We track max widths to auto-adjust the table columns
        # Start with minimums to fit the headers
        col_widths = {
            "field": len("Field Name"),
            "type": len("Cardinality"),
            "target": len("Target Model"),
        }

        for field in model._meta.get_fields():
            if not field.is_relation:
                continue

            # Determine Direction
            is_reverse = isinstance(field, ForeignObjectRel)

            # Determine Cardinality & Tip
            if field.many_to_one:
                cardinality = "Many-to-One"
                admin_tip = "select_related"
            elif field.one_to_one:
                cardinality = "One-to-One"
                admin_tip = "select_related"
            elif field.one_to_many:
                cardinality = "One-to-Many"
                admin_tip = "prefetch_related"
            elif field.many_to_many:
                cardinality = "Many-to-Many"
                admin_tip = "prefetch_related"
            elif not field.concrete:
                # This catches GenericForeignKey, which is single-valued
                # but requires prefetch_related because it joins to dynamic tables.
                cardinality = "Generic FK"
                admin_tip = "prefetch_related"
            else:
                cardinality = "Unknown"
                admin_tip = ""

            # Determine Labels
            if is_reverse:
                field_name = field.get_accessor_name()
                related_model = field.related_model.__name__
                target_list = incoming_rows
            else:
                field_name = field.name
                related_model = field.related_model.__name__
                target_list = outgoing_rows

            # Update Widths (check if this row is wider than current max)
            col_widths["field"] = max(col_widths["field"], len(field_name))
            col_widths["type"] = max(col_widths["type"], len(cardinality))
            col_widths["target"] = max(col_widths["target"], len(related_model))

            # Store tuple
            target_list.append((field_name, cardinality, related_model, admin_tip))

        # Add a little padding to the columns for visual breathing room
        w_field = col_widths["field"] + 2
        w_type = col_widths["type"] + 2
        w_target = col_widths["target"] + 2

        # 2. Helper function to print a table
        def print_table(title, rows):
            rows.sort()
            self.stdout.write(f"\n{self.style.MIGRATE_HEADING(title)}")
            if not rows:
                self.stdout.write("  None")
                return

            # Print Header
            header = f"{'Field Name':<{w_field}}{'Cardinality':<{w_type}}{'Target Model':<{w_target}}Suggested admin Optimization"
            self.stdout.write(header)
            self.stdout.write("-" * len(header))

            # Print Rows
            for name, card, target, tip in rows:
                # Color code the field name
                name_colored = self.style.WARNING(f"{name:<{w_field}}")
                target_colored = self.style.SUCCESS(f"{target:<{w_target}}")

                self.stdout.write(f"{name_colored}{card:<{w_type}}{target_colored}{tip}")

        # 3. Output
        self.stdout.write(f"Model: {model._meta.label}")
        print_table("OUTGOING (Forward) Relationships", outgoing_rows)
        print_table("INCOMING (Reverse) Relationships", incoming_rows)
