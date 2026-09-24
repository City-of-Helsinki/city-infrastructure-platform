from auditlog.cid import set_cid
from auditlog.middleware import AuditlogMiddleware as BaseAuditlogMiddleware

from auditlog_custom.context import safe_set_extra_data


class AuditlogMiddleware(BaseAuditlogMiddleware):
    """
    Customized auditlog middleware to plug PII leaks from django-auditlog originating from its provided middleware.
    """

    def __call__(self, request):
        set_cid(request)

        with safe_set_extra_data(context_data=self.get_extra_data(request)):
            return self.get_response(request)
