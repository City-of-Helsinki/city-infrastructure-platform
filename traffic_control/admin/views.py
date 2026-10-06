from django.contrib.admin import ModelAdmin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Page, Paginator
from django.db.models import QuerySet
from django.http import HttpRequest, JsonResponse
from django.views.generic import View

from traffic_control.models import TrafficControlDeviceType

__all__ = ("DeviceTypeAutocompleteJsonView",)


class DeviceTypeAutocompleteJsonView(View):
    """Search endpoint feeding the device type select2 widget on the device type tag admin page.

    Django's own admin autocomplete view is not part of the public API and it does not support
    reverse many-to-many relations as the source field, which is what the tag page needs. This
    view is a dedicated replacement built only on documented APIs. It always searches
    ``TrafficControlDeviceType`` objects, so the ``app_label``, ``model_name`` and ``field_name``
    query parameters sent by the shared admin javascript are ignored.
    """

    admin_site = None
    paginate_by = 20

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        """Return the device types matching the search term in the select2 response format.

        Args:
            request (HttpRequest): Request carrying the ``term`` and ``page`` query parameters.

        Returns:
            JsonResponse: Object with a ``results`` list and a ``pagination`` object.

        Raises:
            PermissionDenied: If the user may not view device types.
        """
        model_admin = self.admin_site.get_model_admin(TrafficControlDeviceType)
        if not model_admin.has_view_permission(request):
            raise PermissionDenied

        page = self._get_page(model_admin, request)

        return JsonResponse(
            {
                "results": [self._serialize(device_type) for device_type in page],
                "pagination": {"more": page.has_next()},
            }
        )

    def _get_page(self, model_admin: ModelAdmin, request: HttpRequest) -> Page:
        """Paginate the search results of the current request.

        Args:
            model_admin (ModelAdmin): Admin of the searched device type model.
            request (HttpRequest): Request carrying the ``term`` and ``page`` query parameters.

        Returns:
            Page: The requested page of matching device types.
        """
        queryset = self._get_queryset(model_admin, request)
        paginator = Paginator(queryset, self.paginate_by)

        return paginator.get_page(request.GET.get("page") or 1)

    @staticmethod
    def _get_queryset(model_admin: ModelAdmin, request: HttpRequest) -> QuerySet:
        """Search the device types visible to the user with the admin's own search configuration.

        Args:
            model_admin (ModelAdmin): Admin of the searched device type model.
            request (HttpRequest): Request carrying the ``term`` query parameter.

        Returns:
            QuerySet: Device types matching the search term.
        """
        queryset = model_admin.get_queryset(request)
        queryset, search_use_distinct = model_admin.get_search_results(
            request,
            queryset,
            request.GET.get("term", ""),
        )
        if search_use_distinct:
            queryset = queryset.distinct()

        return queryset

    @staticmethod
    def _serialize(device_type: TrafficControlDeviceType) -> dict:
        """Convert a device type into a select2 result object.

        Args:
            device_type (TrafficControlDeviceType): The device type to convert.

        Returns:
            dict: Object with the ``id`` and ``text`` keys expected by select2.
        """
        return {"id": str(device_type.pk), "text": str(device_type)}
