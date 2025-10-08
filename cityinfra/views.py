from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from health_check.views import MainView


class HealthCheckView(MainView):
    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        status_code = status_code = 200 if not self.errors else 500
        status = "OK" if not self.errors else "NOT_OK"

        response = {
            "status": status,
            "service": "city-infrastructure-platform",
            "environment": settings.ENVIRONMENT_NAME,
            "version": settings.VERSION,
        }

        return JsonResponse(response, status=status_code)


class CloudUploadProxyView(View):
    @classmethod
    def get_storage(cls):
        pass

    @classmethod
    def get_cloud_path(cls, filepath):
        return f"some_base_path/{filepath}"

    def get(self, request, filepath):
        pass

    def post(self, request, filepath):
        pass

    def put(self, request, filepath):
        pass

    def delete(self, request, filepath):
        pass
