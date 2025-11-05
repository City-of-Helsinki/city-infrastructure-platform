import mimetypes

from django.conf import settings
from django.core.files.storage import storages
from django.http import FileResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from health_check.views import MainView

from traffic_control.file_registry import UPLOAD_PATH_TO_MODEL_MAP


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

    def get(self, request, upload_folder, model_name, file_id):
        lookup_path = f"{upload_folder}/{model_name}"
        model_class = UPLOAD_PATH_TO_MODEL_MAP.get(lookup_path)

        # NOTE (2025-11-05 thiago)
        # We need to check both for the existence of the table row and the existence of the file in the storage, since
        # the storage may be managed separately from django and the permissions cannot be checked without django
        if not model_class:
            return HttpResponseBadRequest("Invalid file path.")
        file_path = f"{upload_folder}/{model_name}/{file_id}"
        file_obj = get_object_or_404(model_class, file=file_path)

        if not file_obj.is_public:
            user = request.user
            if not user or not user.is_authenticated:
                return HttpResponseForbidden("You do not have permission to view this file.")

            permission_name = f"{model_class._meta.app_label}." f"view_{model_class._meta.model_name}"
            if not user.has_perm(permission_name) and not user.has_perm(permission_name, file_obj):
                return HttpResponseForbidden("You do not have permission to view this file.")

        file_handle = self.get_storage().open(file_path)
        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or "application/octet-stream"
        response = FileResponse(file_handle, content_type=content_type)
        response["Content-Disposition"] = f'inline; filename="{file_id}"'
        return response
