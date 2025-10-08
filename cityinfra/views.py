import mimetypes

from django.conf import settings
from django.core.files.storage import storages
from django.http import FileResponse, Http404, JsonResponse
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


class FileProxyView(View):
    @classmethod
    def get_storage(cls):
        return storages["default"]

    def get(self, _request, upload_folder, model_name, file_id):
        # TODO authenticate the request

        storage_path = f"{upload_folder}/{model_name}/{file_id}"
        if not self.get_storage().exists(storage_path):
            raise Http404("File not found.")

        file_handle = self.get_storage().open(storage_path)
        content_type, _ = mimetypes.guess_type(storage_path)
        content_type = content_type or "application/octet-stream"
        response = FileResponse(file_handle, content_type=content_type)
        response["Content-Disposition"] = f'inline; filename="{file_id}"'
        return response
