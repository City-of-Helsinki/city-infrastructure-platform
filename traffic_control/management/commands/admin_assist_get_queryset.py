from django.apps import apps
from django.contrib import admin
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Introspects list_display, __str__, and functors to suggest an optimized get_queryset."

    def add_arguments(self, parser):
        parser.add_argument("app_label", type=str)
        parser.add_argument("model_name", type=str)

    def handle(self, *args, **options):
        app_label = options["app_label"]
        model_name = options["model_name"]

        # 1. Load Model and Admin
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            raise CommandError(f"Model {model_name} not found.")

        if model not in admin.site._registry:
            raise CommandError(f"Model {model_name} is not registered in the Admin.")

        admin_instance = admin.site._registry[model]

        # 2. Collect all requirements
        data_requirements = set()
        queryset_transforms = set()
        data_requirements.add("pk")

        self.stdout.write(self.style.MIGRATE_HEADING(f"Introspecting {model.__name__}Admin..."))

        # Helper function to inspect a callable for our decorators
        def inspect_callable(func):
            if not func:
                return
            if hasattr(func, "required_fields"):
                data_requirements.update(func.required_fields)
            if hasattr(func, "queryset_transforms"):
                queryset_transforms.update(func.queryset_transforms)

        # --- Check Model.__str__ ---
        if hasattr(model, "__str__"):
            inspect_callable(model.__str__)
            if hasattr(model.__str__, "required_fields"):
                self.stdout.write(f"  Found requirements in {model.__name__}.__str__")

        # --- Check list_display ---
        for item in admin_instance.list_display:
            # Case A: String (Field name OR Method name)
            if isinstance(item, str):
                if self.is_model_field(model, item):
                    data_requirements.add(item)
                else:
                    # It must be a method/property on the Admin or the Model
                    func = getattr(admin_instance, item, None)
                    if not func:
                        func = getattr(model, item, None)

                    inspect_callable(func)

            # Case B: Direct Callable (Functor)
            elif callable(item):
                inspect_callable(item)

        # 3. Analyze Relationships & Build Optimization Sets
        select_related_paths = set()
        prefetch_related_paths = set()
        only_fields = set()

        for req in data_requirements:
            self.analyze_requirement(model, req, select_related_paths, prefetch_related_paths, only_fields)

        # 4. Generate Code
        self.print_snippet(
            model.__name__, select_related_paths, prefetch_related_paths, only_fields, queryset_transforms
        )

    def is_model_field(self, model, field_name):
        try:
            model._meta.get_field(field_name)
            return True
        except FieldDoesNotExist:
            return False

    def analyze_requirement(self, model, path, selects, prefetches, onlys, root_model=None):
        """
        Traverses a field path step-by-step.
        """
        if root_model is None:
            root_model = model

        parts = path.split("__")
        current_model = model
        current_path_parts = []

        is_projection_candidate = True

        for i, part in enumerate(parts):
            try:
                field = current_model._meta.get_field(part)
            except FieldDoesNotExist:
                # Not a model field (likely a property, method, or annotation)
                is_projection_candidate = False
                break

            current_path_parts.append(part)
            path_so_far = "__".join(current_path_parts)

            if field.is_relation:
                # 1. Forward Relation (ForeignKey, OneToOne) -> Use JOIN
                if field.many_to_one or field.one_to_one:
                    selects.add(path_so_far)

                    # RECURSION: Check if we are printing this object (__str__ dependencies)
                    if i == len(parts) - 1:
                        related_model = field.related_model
                        if hasattr(related_model, "__str__") and hasattr(related_model.__str__, "required_fields"):
                            for req in related_model.__str__.required_fields:
                                full_child_path = f"{path_so_far}__{req}"
                                self.analyze_requirement(
                                    root_model, full_child_path, selects, prefetches, onlys, root_model=root_model
                                )

                    if hasattr(field, "related_model") and field.related_model:
                        current_model = field.related_model

                # 2. Reverse/M2M Relation -> Use PREFETCH
                elif field.many_to_many or field.one_to_many:
                    prefetches.add(path_so_far)
                    # M2M fields cannot be in .only()
                    is_projection_candidate = False
                    break

                    # Add the path to .only() if it's a valid field (Concrete OR ForeignKey)
        if is_projection_candidate:
            onlys.add(path)

    def print_snippet(self, model_name, selects, prefetches, onlys, transforms):
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("SUGGESTED OPTIMIZATION"))
        self.stdout.write("=" * 50 + "\n")

        lines = []
        lines.append("    def get_queryset(self, request):")
        lines.append("        # NOTE: This get_queryset was generated by the admin_assist_get_queryset command.")
        lines.append("        # If it is in need of updates, try generating a new one with the command again.")
        lines.append("")
        lines.append("        qs = super().get_queryset(request)")

        selects = sorted(list(selects))
        prefetches = sorted(list(prefetches))
        onlys = sorted(list(onlys))
        transforms = sorted(list(transforms))

        # 1. Transformations (Annotations)
        if transforms:
            lines.append("")
            lines.append("        # Applying Custom Transformations")
            for t in transforms:
                # CHANGED: Use 'self' to refer to methods on the Admin class
                lines.append(f"        qs = self.{t}(qs)")

        # 2. Joins
        if selects:
            lines.append("")
            lines.append("        # Optimizing Forward Relations (Joins)")
            lines.append("        qs = qs.select_related(")
            for s in selects:
                lines.append(f"            '{s}',")
            lines.append("        )")

        # 3. Prefetches
        if prefetches:
            lines.append("")
            lines.append("        # Optimizing Reverse/M2M Relations")
            lines.append("        qs = qs.prefetch_related(")
            for p in prefetches:
                lines.append(f"            '{p}',")
            lines.append("        )")

        # 4. Projections
        if onlys:
            lines.append("")
            lines.append("        # Limiting Columns (Projection)")
            lines.append("        qs = qs.only(")
            for o in onlys:
                lines.append(f"            '{o}',")
            lines.append("        )")

        lines.append("")
        lines.append("        return qs")

        self.stdout.write("\n".join(lines))
