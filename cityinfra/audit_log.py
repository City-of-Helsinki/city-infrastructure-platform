from django.utils.encoding import smart_str


def resolve_actor(actor) -> dict:  # TODO PUT SOMEWHERE SENSIBLE
    import auditlog.diff
    from resilient_logger.utils import parse_uuid

    actor_data = {
        "uuid": None,
        "version": None,
        "email": None,
    }

    if not actor:
        print("resolve_actor is", actor_data)
        return actor_data

    raw_uuid = getattr(actor, "uuid", None)
    raw_email = getattr(actor, "email", None)
    parsed_uuid = parse_uuid(raw_uuid)

    if parsed_uuid:
        actor_data["uuid"] = str(parsed_uuid)
        actor_data["version"] = parsed_uuid.version
    if raw_email:
        actor_data["email"] = auditlog.diff.mask_str(raw_email)

    print("resolve_actor is", actor_data)

    return actor_data


def safe_object_repr(input):
    """
    Safely builds a string representation without invoking input.__str__().
    Formats as 'ModelName (pk)'.
    """
    from django.db import models

    if isinstance(input, models.Model):
        model_name = input._meta.object_name
        pk_val = input.pk

        print(f"safe_object_repr is {model_name} ({pk_val})")
        return f"{model_name} ({pk_val})"

    print(f"safe_object_repr is {smart_str(input)}")
    return smart_str(input)
