from auditlog.middleware import AuditlogMiddleware as BaseAuditlogMiddleware


class AuditlogMiddleware(BaseAuditlogMiddleware):
    """
    Customized Auditlog middleware to disable logging client IP address.
    `django-auditlog` version 2.3.0 doesn't have a configuration option
    to disable IP address logging, so this is a workaround.

    See issue https://github.com/jazzband/django-auditlog/issues/524
    """

    @staticmethod
    def _get_remote_addr(request):
        return None
