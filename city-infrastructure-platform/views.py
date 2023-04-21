from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from health_check.views import MainView


class HealthCheckView(MainView):
    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        status_code = status_code = 200 if not self.errors else 500
        status = "OK" if not self.errors else "NOT_OK"

        response = {"status": status}

        return JsonResponse(response, status=status_code)
