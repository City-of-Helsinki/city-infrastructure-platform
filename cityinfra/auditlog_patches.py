import auditlog
import auditlog.context
import auditlog.diff
from resilient_logger.utils import parse_uuid


def resolve_actor(actor) -> dict:
    # Add actor email
    actor_data = {
        "uuid": None,
        "version": None,
        "email": None,
    }

    if not actor:
        return actor_data

    raw_uuid = getattr(actor, "uuid", None)
    raw_email = getattr(actor, "email", None)
    parsed_uuid = parse_uuid(raw_uuid)

    if parsed_uuid:
        actor_data["uuid"] = str(parsed_uuid)
        actor_data["version"] = parsed_uuid.version
    if raw_email:
        actor_data["email"] = auditlog.diff.mask_str(raw_email)

    return actor_data


def patch_auditlog_pii_leak():
    """
    Monkey patches django-auditlog to prevent leaking the actor's email
    into the LogEntry instance.
    """
    # Save a reference to the original function
    original_set_actor = auditlog.context._set_actor
    mask_function = auditlog.diff.get_mask_function()

    # Define our wrapper
    def scrubbed_set_actor(auditlog_data, instance, sender):
        # 1. Let the original function do its normal work (setting actor, etc.)
        original_set_actor(auditlog_data, instance, sender)

        # 2. Scrub the PII it just set
        if getattr(instance, "actor_email", None):
            instance.actor_email = mask_function(instance.actor_email)

    # Overwrite the function in the module
    auditlog.context._set_actor = scrubbed_set_actor
