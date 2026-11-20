"""Guard: import-export must turn blank cells into "" for every optional non-nullable string field."""

import inspect
from importlib import import_module
from pkgutil import iter_modules
from typing import Iterator

from import_export.resources import ModelResource

from traffic_control.serializers.common import accepts_null_as_empty_string

RESOURCE_PACKAGES = ("traffic_control.resources", "city_furniture.resources")


def _resource_classes() -> Iterator[type[ModelResource]]:
    """Yield every concrete ModelResource defined in the project's resource packages.

    Yields:
        type[ModelResource]: Resource classes with a model.
    """
    for package_name in RESOURCE_PACKAGES:
        package = import_module(package_name)
        for module_info in iter_modules(package.__path__):
            module = import_module(f"{package_name}.{module_info.name}")
            for _name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, ModelResource) and obj.__module__ == module.__name__ and obj._meta.model:
                    yield obj


def test__all_resources__import_blank_cells_as_empty_string_for_optional_string_fields() -> None:
    """Blank cells come out of xlsx files as None; every resource must turn them into ""."""
    checked = 0
    failures = []
    for resource_class in _resource_classes():
        model = resource_class._meta.model
        for field_name, field in resource_class().fields.items():
            try:
                model_field = model._meta.get_field(field.attribute)
            except Exception:
                continue
            if not accepts_null_as_empty_string(model_field):
                continue
            checked += 1
            cleaned = field.clean({field.column_name: None})
            if cleaned != "":
                failures.append(f"{resource_class.__module__}.{resource_class.__name__}.{field_name} -> {cleaned!r}")

    assert checked > 0
    assert failures == []
