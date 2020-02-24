import logging

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

logger = logging.getLogger("azure_client_ip")


class AzureClientIPMiddleware:
    def __init__(self, get_response):

        # Only use this middleware if we have defined the deployment to be in Azure environment.
        if not settings.AZURE_DEPLOYMENT:
            raise MiddlewareNotUsed

        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)

        return self.get_response(request)

    @staticmethod
    def process_request(request):
        if "HTTP_X_CLIENT_IP" in request.META:
            request.META["HTTP_X_FORWARDED_FOR"] = request.META["HTTP_X_CLIENT_IP"]
        return None
