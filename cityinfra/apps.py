from django.apps import AppConfig


def patch_auditlog_pii_leak():
    """
    Monkey patches django-auditlog to prevent leaking the actor's email
    into the LogEntry instance.
    """
    import auditlog.context
    import auditlog.diff

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


class CityInfraConfig(AppConfig):
    name = "cityinfra"

    def ready(self):
        patch_auditlog_pii_leak()
