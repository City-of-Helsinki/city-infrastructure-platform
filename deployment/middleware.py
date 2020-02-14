import logging

from django.http import HttpResponse

logger = logging.getLogger("healthz")


class HealthCheckMiddleware(object):
    """
    Health check middleware

    ## Usage
    Put the middleware at the very top of your Middleware chain so that
    no other middleware such as auth or other security catches the request
    before this one. Note that the middleware then bypasses all host checks
    as well, including ALLOWED_HOSTS.

    ## Description
    Health checks are part of several deployment strategies to
    know if a service is up and running and healthy enough to response
    to simple requests. While it might not signal that a service is
    ready, it does signal that it is up and running. The main use-case
    for health checks to for load balancers to check if a service is
    up so so that it can tell the end user that a deployment is successful
    or in the case or red-green or canary deployment to signal that the
    service is up and the next step in the deployment may be started.

    ## Why /healthz and not /health
    https://stackoverflow.com/a/43381061
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        if request.method == "GET":
            if request.path == "/readiness":
                return self.readiness(request)
            elif request.path == "/healthz":
                return self.healthz(request)
        return self.get_response(request)

    def healthz(self, request):
        """
        Returns that the server is alive.
        """
        return HttpResponse("OK")

    def readiness(self, request):
        """
        Returns if the service is ready.

        Override this method to implement custom
        readyness checks for the application.
        """
        return HttpResponse("OK")
