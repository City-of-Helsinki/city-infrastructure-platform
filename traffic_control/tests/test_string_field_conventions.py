"""Guards for the string field convention: ``null`` and ``blank`` are written out, and ``null`` is ``False``.

Optional string fields use ``blank=True, null=False`` so that ``""`` is their only "no value" state.
Required ones use ``blank=False, null=False``. Both are written out even where they are the default,
so that each declaration shows at a glance whether the field is optional and how "no value" is stored.

What the guards do not cover: django-enumfields ``EnumField``s (the library turns ``""`` into
``None``, so their "no value" is stored as NULL; Django's native ``TextChoices`` store ``""`` and
follow the convention above), the three field names listed below, the ``users`` app, and fields
that are not declared as a direct ``models.<Class>(...)`` call in a model module.
"""

import ast
import inspect
from typing import Iterator

from django.apps import apps
from django.db import models
from enumfields import EnumField

STRING_FIELD_CLASSES = ("CharField", "TextField", "URLField", "SlugField", "EmailField")
PROJECT_APPS = (
    "city_furniture",
    "command_tracker",
    "maintenance_mode",
    "map",
    "site_alert",
    "traffic_control",
)
# users is left out: User only has string fields inherited from helusers, incl. a nullable department_name.
# Optional fields that most models have under a unique constraint: NULLs never collide in Postgres,
# but "" would. They are nullable on every model, also the few without such a constraint.
NULLABLE_ON_PURPOSE = {"source_id", "source_name", "diary_number"}


def _model_modules() -> Iterator[object]:
    """Yield every module that defines a model or an abstract base of a model in the project's apps.

    Yields:
        object: Imported module.
    """
    seen = set()
    for model in apps.get_models():
        for klass in model.__mro__:
            module = inspect.getmodule(klass)
            if module and module.__name__.split(".")[0] in PROJECT_APPS and module.__name__ not in seen:
                seen.add(module.__name__)
                yield module


def test__string_fields__state_null_and_blank_explicitly() -> None:
    """Every string field declaration in the project's model modules passes both null=... and blank=..."""
    checked = 0
    missing = []
    for module in _model_modules():
        for node in ast.walk(ast.parse(inspect.getsource(module))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in STRING_FIELD_CLASSES
                and getattr(node.func.value, "id", None) == "models"
            ):
                checked += 1
                unstated = {"null", "blank"} - {keyword.arg for keyword in node.keywords}
                if unstated:
                    missing.append(f"{module.__name__}:{node.lineno} does not state {', '.join(sorted(unstated))}")

    assert checked > 0
    assert missing == []


def test__string_fields__are_not_nullable() -> None:
    """No string field is nullable except the documented ones."""
    nullable = [
        f"{model.__name__}.{field.name}"
        for model in apps.get_models()
        if model.__module__.split(".")[0] in PROJECT_APPS
        for field in model._meta.local_fields
        if isinstance(field, (models.CharField, models.TextField))
        and field.null
        and not isinstance(field, EnumField)
        and field.name not in NULLABLE_ON_PURPOSE
    ]

    assert nullable == []
