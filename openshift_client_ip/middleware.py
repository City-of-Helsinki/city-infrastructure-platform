import ipaddress
import logging

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

logger = logging.getLogger("openshift_client_ip")


class OpenShiftClientIPMiddleware:
    def __init__(self, get_response):
        # Only use this middleware if we have defined the deployment to be in OpenShift environment.
        if not settings.OPENSHIFT_DEPLOYMENT:
            raise MiddlewareNotUsed

        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)

        return self.get_response(request)

    @staticmethod
    def process_request(request):
        if "HTTP_X_FORWARDED_FOR" in request.META:
            xff = request.META["HTTP_X_FORWARDED_FOR"]

            request.META["HTTP_X_FORWARDED_FOR_ORIGINAL"] = xff

            # Test if field is a valid IP address
            try:
                ipaddress.ip_address(xff)
            except ValueError:
                # If there are proxy IPs listed, the first one should be client IP
                xff = xff.split(",")[0]

                # Remove port number from the end of IP if there is such
                xff = xff.split(":")[0]

                try:
                    ipaddress.ip_address(xff)
                except ValueError:
                    raise ValueError(f"Could not parse IP from '{xff}'.")

            # Overwrite validated client IP in meta
            request.META["HTTP_X_FORWARDED_FOR"] = xff

        return None
