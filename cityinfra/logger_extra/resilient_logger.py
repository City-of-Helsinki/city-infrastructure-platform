import uuid
from typing import Any

from logger_extra.extras.resilient_logger import resolve_actor_with_masked_email


def _get_field(target: object, key: str) -> Any:
    """
    Functions as either getattr(object, key, None) or dict.get(key, None)
    """
    if isinstance(target, dict):
        return target.get(key, None)
    return getattr(target, key, None)


def _parse_uuid(value: str | uuid.UUID | None) -> uuid.UUID | None:
    """
    Parses the given value into a UUID instance or returns None if parsing fails.
    """
    if value is None:
        return None

    if isinstance(value, uuid.UUID):
        return value

    try:
        return uuid.UUID(value)
    except (ValueError, TypeError):
        return None


def cityinfra_resolve_actor_with_masked_email(actor) -> dict:
    """
    Adds the city-infrastructure-platform primary key to the actor object in the auditlog.
    """
    actor_data = resolve_actor_with_masked_email(actor)
    actor_data["cityinfra_pk"] = None

    raw_cityinfra_pk = _get_field(actor, "pk")
    parsed_pk = _parse_uuid(raw_cityinfra_pk)

    if parsed_pk:
        actor_data["cityinfra_pk"] = parsed_pk

    return actor_data
