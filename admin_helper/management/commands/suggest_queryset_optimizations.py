import datetime
import importlib
import sys
from typing import Callable

from django.contrib import admin
from django.contrib.admin.options import BaseModelAdmin
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db import models


def indent(level: int, text: str) -> str:
    """Helper to enforce exactly 4-space indentation per level."""
    return ("    " * level) + text


def flatten_fields(fields_iterable):
    """Recursive generator to flatten nested field tuples/lists."""
    for item in fields_iterable:
        if isinstance(item, (tuple, list)):
            yield from flatten_fields(item)
        else:
            yield item


def append_via(source: str, via_name: str) -> str:
    """Formats function chains elegantly, e.g. 'list_display (via func1 -> func2)'"""
    if "(via " in source and source.endswith(")"):
        return f"{source[:-1]} -> {via_name})"
    return f"{source} (via {via_name})"


def deduplicate_sources(sources: list[str]) -> list[str]:
    """
    Returns a sorted list of unique sources.
    Folds intermediate subchains and prevents branching spam by keeping only
    one trace per root callable.
    """
    unique_sources = sorted(list(set(sources)), key=len, reverse=True)
    cleaned = []
    seen_prefixes = set()

    for src in unique_sources:
        # Identify the root base of the source string to group divergent branches
        if " -> " in src:
            prefix = src.split(" -> ")[0]
        elif "(via " in src and src.endswith(")"):
            prefix = src[:-1]
        else:
            prefix = src

        if prefix not in seen_prefixes:
            seen_prefixes.add(prefix)
            cleaned.append(src)

    return sorted(cleaned)


class AdminQuerySetGenerator:
    """Encapsulates the logic for analyzing an admin class and generating a queryset method."""

    def __init__(
        self, admin_class: type[BaseModelAdmin], model: models.Model, error_handler=None, warning_handler=None
    ):
        self.admin_class = admin_class
        self.model = model
        self.is_inline = issubclass(admin_class, admin.options.InlineModelAdmin)
        self.visited_funcs = set()
        self.error = error_handler or (lambda msg: sys.stderr.write(f"ERROR: {msg}\n"))
        self.warn = warning_handler or (lambda msg: sys.stderr.write(f"WARNING: {msg}\n"))

        self.reqs = {
            "list": {"select": {}, "prefetch": {}, "annotations": set()},
            "detail": {"select": {}, "prefetch": {}, "annotations": set()},
        }

    def generate(self) -> str:
        self.discover_fields()
        return self.generate_output_string()

    def discover_fields(self):
        # 1. List Views (Standard Admins Only)
        list_display = getattr(self.admin_class, "list_display", [])
        for field in list_display:
            self.process_field(field, "list", "list_display")

        # 2. Detail Views (Standard & Inline)
        detail_sources = [
            ("readonly_fields", getattr(self.admin_class, "readonly_fields", [])),
            ("fields", getattr(self.admin_class, "fields", [])),
        ]

        fieldsets = getattr(self.admin_class, "fieldsets", [])
        if fieldsets:
            fieldset_fields = []
            for fs in fieldsets:
                if len(fs) > 1 and isinstance(fs[1], dict) and "fields" in fs[1]:
                    fieldset_fields.extend(list(flatten_fields(fs[1]["fields"])))
            detail_sources.append(("fieldsets", fieldset_fields))

        for source_name, fields in detail_sources:
            for field in fields or []:
                self.process_field(field, "detail", source_name)

    def traverse_path(self, path: str, view_type: str, source_attr: str):
        parts = path.split("__")
        current_model = self.model
        orm_path = []
        is_prefetch = False
        relation_labels = []

        for i, part in enumerate(parts):
            try:
                field = current_model._meta.get_field(part)
                if not field.is_relation:
                    break

                orm_path.append(part)

                if field.many_to_many:
                    rel_type, is_prefetch = "n:n", True
                elif field.one_to_many:
                    rel_type, is_prefetch = "1:n", True
                elif field.many_to_one:
                    rel_type = "n:1"
                elif field.one_to_one:
                    rel_type = "1:1"
                else:
                    rel_type = "unknown"

                relation_labels.append(rel_type)
                current_path = "__".join(orm_path)

                label_suffix = " relation chain" if len(relation_labels) > 1 else " relation"
                final_label = f"{rel_type}{label_suffix}"

                target_dict = self.reqs[view_type]["prefetch" if is_prefetch else "select"]
                if current_path not in target_dict:
                    target_dict[current_path] = {"rel_type": final_label, "sources": []}
                target_dict[current_path]["sources"].append(source_attr)

                current_model = field.related_model

                if i == len(parts) - 1:
                    self.inspect_dunder_str(current_model, current_path, view_type, source_attr)

            except FieldDoesNotExist:
                remainder = "__".join(parts[i:])
                parent_path = "__".join(orm_path)
                self.inspect_callable(current_model, remainder, parent_path, view_type, source_attr)
                break

    def inspect_dunder_str(self, model, parent_path: str, view_type: str, source_attr: str):
        """Evaluates explicit __str__ methods in models."""
        str_func = getattr(model, "__str__", None)
        if str_func and str_func is not models.Model.__str__:
            new_source = append_via(source_attr, f"{model.__name__}.__str__")
            self.process_callable_logic(
                str_func, parent_path, view_type, new_source, attr_name="__str__", owner_name=model.__name__
            )

    def inspect_callable(self, current_model, remainder: str, parent_path: str, view_type: str, source_attr: str):
        """Evaluates callable methods in the admin class or a model in the chain. Prioritizes admin class methods."""
        # 1. Try finding it on the Admin Class
        callable_obj = getattr(self.admin_class, remainder, None)
        owner_name = self.admin_class.__name__

        # 2. Try finding it on the Model
        if not callable_obj:
            callable_obj = getattr(current_model, remainder, None)
            owner_name = current_model.__name__

        if not callable_obj:
            self.error(f"Could not resolve '{remainder}' on {self.admin_class.__name__} or {current_model.__name__}.")
            return

        func_name = getattr(callable_obj, "__name__", remainder)
        new_source = append_via(source_attr, func_name)

        self.process_callable_logic(
            callable_obj, parent_path, view_type, new_source, attr_name=remainder, owner_name=owner_name
        )

    def process_field(self, field: str | Callable, view_type: str, source_name: str):
        if callable(field):
            func_name = getattr(field, "__name__", str(field))
            self.process_callable_logic(
                field,
                "",
                "detail",
                append_via(source_name, func_name),
                attr_name=func_name,
                owner_name="Direct Callable",
            )
        elif isinstance(field, str):
            self.traverse_path(field, view_type, source_name)

    def process_callable_logic(
        self,
        callable_obj: Callable,
        parent_path: str,
        view_type: str,
        source_attr: str,
        attr_name=None,
        owner_name=None,
    ):
        if (callable_obj, view_type) in self.visited_funcs:
            return
        self.visited_funcs.add((callable_obj, view_type))

        has_annotation = hasattr(callable_obj, "annotation_callback")
        has_required = hasattr(callable_obj, "required_fields")

        if not has_annotation and not has_required:
            # Fallback to __name__ if attr_name wasn't provided, and then to str(obj)
            name = attr_name or getattr(callable_obj, "__name__", str(callable_obj))
            location = f" on {owner_name}" if owner_name else ""
            self.warn(f"Callable '{name}'{location} lacks decorator metadata.")
            return

        if has_annotation:
            callback = getattr(callable_obj, "annotation_callback")
            callback_name = callback.__name__
            if hasattr(self.admin_class, callback_name) and getattr(self.admin_class, callback_name) == callback:
                callback_str = f"self.{callback_name}(qs)"
            else:
                callback_str = f"{callback_name}(qs)"
            self.reqs[view_type]["annotations"].add((callback_str, source_attr))

        if has_required:
            for req_field in getattr(callable_obj, "required_fields"):
                full_path = f"{parent_path}__{req_field}" if parent_path else req_field
                self.traverse_path(full_path, view_type, source_attr)

    def build_queryset_chain(self, level: int, selects: dict, prefetches: dict) -> list[str]:
        """Builds a queryset .select_related and/or .prefetch_related call chain with the relevant fields."""
        lines = []
        if not selects and not prefetches:
            lines.append(indent(level, "return qs"))
            return lines

        lines.append(indent(level, "return qs \\"))

        if selects:
            lines.append(indent(level + 1, ".select_related("))
            for path, data in sorted(selects.items()):
                srcs = ", ".join(deduplicate_sources(data["sources"]))
                lines.append(indent(level + 2, f'"{path}",  # {data["rel_type"]} in {srcs} # noqa: E501'))
            lines.append(indent(level + 1, ") \\"))

        if prefetches:
            lines.append(indent(level + 1, ".prefetch_related("))
            for path, data in sorted(prefetches.items()):
                srcs = ", ".join(deduplicate_sources(data["sources"]))
                lines.append(indent(level + 2, f'"{path}",  # {data["rel_type"]} in {srcs} # noqa: E501'))
            lines.append(indent(level + 1, ") \\"))

        lines[-1] = lines[-1].rstrip(" \\")
        return lines

    def generate_output_string(self) -> str:
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(" ", timespec="seconds")
        class_name = self.admin_class.__name__

        lines = [
            indent(1, f"# Generated for {class_name} at {timestamp}"),
            indent(1, "def get_queryset(self, request):"),
            indent(2, "qs = super().get_queryset(request)"),
        ]

        if self.is_inline:
            detail_requirements = self.reqs["detail"]
            for callback_str, source in sorted(detail_requirements["annotations"]):
                lines.append(indent(2, f"qs = {callback_str}  # from {source}"))
            lines.extend(self.build_queryset_chain(2, detail_requirements["select"], detail_requirements["prefetch"]))

        else:
            lines.append(indent(2, "resolver_match = getattr(request, 'resolver_match', None)"))
            lines.append(indent(2, "if not resolver_match or not resolver_match.url_name:"))
            lines.append(indent(3, "return qs"))
            lines.append("")

            list_requirements = self.reqs["list"]
            detail_requirements = self.reqs["detail"]

            lines.append(indent(2, "if resolver_match.url_name.endswith('_changelist'):"))
            if list_requirements["annotations"] or list_requirements["select"] or list_requirements["prefetch"]:
                for callback_str, source in sorted(list_requirements["annotations"]):
                    lines.append(indent(3, f"qs = {callback_str}  # from {source}"))
                lines.extend(self.build_queryset_chain(3, list_requirements["select"], list_requirements["prefetch"]))
            else:
                lines.append(indent(3, "return qs"))

            lines.append(indent(2, "elif resolver_match.url_name.endswith('_change'):"))
            if detail_requirements["annotations"] or detail_requirements["select"] or detail_requirements["prefetch"]:
                for callback_str, source in sorted(detail_requirements["annotations"]):
                    lines.append(indent(3, f"qs = {callback_str}  # from {source}"))
                lines.extend(
                    self.build_queryset_chain(3, detail_requirements["select"], detail_requirements["prefetch"])
                )
            else:
                lines.append(indent(3, "return qs"))

            lines.append("")
            lines.append(indent(2, "return qs"))

        return "\n".join(lines)


class Command(BaseCommand):
    help = "Generates an optimized get_queryset method for a given ModelAdmin."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            "admin_path",
            type=str,
            help='Dotted path to the admin class (e.g., "app.admin.MyModelAdmin")',
        )

    def handle(self, *args, **options):
        admin_path = options["admin_path"]

        try:
            module_path, class_name = admin_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            admin_class = getattr(module, class_name)
        except (ValueError, ImportError, AttributeError) as e:
            raise CommandError(f"Failed to import '{admin_path}': {e}")

        is_inline = issubclass(admin_class, admin.options.InlineModelAdmin)
        model = getattr(admin_class, "model", None) if is_inline else None

        if not is_inline:
            for registered_model, admin_instance in admin.site._registry.items():
                if isinstance(admin_instance, admin_class):
                    model = registered_model
                    break

        if not model:
            raise CommandError(f"Could not resolve the model for '{admin_class.__name__}'.")

        generator = AdminQuerySetGenerator(
            admin_class=admin_class,
            model=model,
            error_handler=lambda msg: self.stderr.write(self.style.ERROR(msg)),
            warning_handler=lambda msg: self.stderr.write(self.style.WARNING(msg)),
        )

        output = generator.generate()
        self.stdout.write(output)
