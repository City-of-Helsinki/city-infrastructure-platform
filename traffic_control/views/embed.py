from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView

from traffic_control.models import MountPlan, MountReal, TrafficSignPlan, TrafficSignReal

# ---------------------------------------------------------------------------
# Shared select_related fragments
# ---------------------------------------------------------------------------

_BASE_SIGN_SELECT_RELATED: list[str] = [
    "device_type",
    "device_type__icon_file",
    "mount_type",
    "owner",
]

_COMMON_ADDITIONAL_SIGN_SELECT_RELATED: list[str] = [*_BASE_SIGN_SELECT_RELATED, "parent"]

# ---------------------------------------------------------------------------
# Shared field-list blocks (sign models)
# ---------------------------------------------------------------------------

_DEVICE_TYPE_FIELDS: list[str] = [
    "device_type.code",
    "device_type.description",
    "device_type.legacy_code",
]

_SIGN_LOCATION_FIELDS: list[str] = [
    "location",
    "road_name",
    "lane_number",
    "lane_type",
    "direction",
    "location_specifier",
    "height",
    "size",
    "reflection_class",
    "surface_class",
]

_VALIDITY_PERIOD_FIELDS: list[str] = [
    "validity_period_start",
    "validity_period_end",
    "seasonal_validity_period_information",
]

# Real-only installed-device fields, split so "installed_by" can be inserted
# between base and suffix for AdditionalSignReal.
_INSTALLED_DEVICE_FIELDS_BASE: list[str] = [
    "condition",
    "installation_date",
    "installation_status",
    "installation_id",
    "installation_details",
]

_INSTALLED_DEVICE_FIELDS_SUFFIX: list[str] = [
    "permit_decision_id",
    "scanned_at",
    "manufacturer",
    "rfid",
    "operation",
    "attachment_url",
]

_SIGN_SOURCE_FIELDS: list[str] = [
    "created_at",
    "updated_at",
    "source_id",
    "source_name",
]

# ---------------------------------------------------------------------------
# Shared field-list blocks (mount models)
# ---------------------------------------------------------------------------

_MOUNT_TYPE_FIELDS: list[str] = [
    "mount_type.code",
    "mount_type.description",
    "mount_type.description_fi",
    "mount_type.digiroad_code",
    "mount_type.digiroad_description",
]

_MOUNT_PHYSICAL_FIELDS: list[str] = [
    "location",
    "height",
    "cross_bar_length",
    "base",
    "portal_type",
    "material",
    "is_foldable",
]

# Note: mount fields use source_name before source_id (unlike sign fields).
_MOUNT_SOURCE_FIELDS: list[str] = [
    "created_at",
    "updated_at",
    "source_name",
    "source_id",
]


class TrafficSignEmbedMixin:
    template_name = "embed/traffic_sign.html"

    @property
    def title(self):
        title = f"{self.model._meta.verbose_name} {self.object.id}"
        device_type = self.object.device_type
        if device_type:
            title += f" - {self.object.device_type.code} {self.object.device_type.description}"
        return title

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            return self.handle_404(request, *args, **kwargs)

    def handle_404(self, request, *args, **kwargs):
        model_name = self.model._meta.verbose_name
        object_id = kwargs.get("pk")
        return HttpResponse(
            _("Error: Could not find %(model_name)s with id %(id)s.") % {"model_name": model_name, "id": object_id},
            content_type="text/plain;charset=utf-8",
            status=404,
        )

    def get_queryset(self):
        return super().get_queryset().active().select_related(*self.traffic_sign_select_related)

    def get_context_data(self, **kwargs):
        parent_context = super().get_context_data(**kwargs)
        traffic_sign = parent_context["object"]
        return {
            **parent_context,
            "title": self.title,
            "traffic_sign_fields": self.get_traffic_sign_fields(traffic_sign),
            "additional_signs": self.get_additional_signs(traffic_sign),
            "mount_fields": self.get_mount_fields(traffic_sign),
        }

    def get_traffic_sign_fields(self, object):
        return self.get_fields_and_values(object, self.traffic_sign_fields)

    def get_additional_signs(self, traffic_sign):
        objects = (
            traffic_sign.additional_signs.active()
            .order_by("-height")
            .select_related(*self.additional_sign_select_related)
        )
        additional_signs = []
        for object in objects:
            content_s_rows = object.get_content_s_rows()
            additional_signs.append(
                {
                    "fields": self.get_fields_and_values(
                        object, self.additional_sign_fields, {"content_s": content_s_rows}
                    ),
                    "object": object,
                }
            )
        return additional_signs

    def get_mount_fields(self, object):
        mount = getattr(object, self.mount_field_name)

        if mount:
            return self.get_fields_and_values(mount, self.mount_fields)
        else:
            return []

    def get_fields_and_values(self, object, field_names, replace_values=None):
        fields_and_values = []

        for field_name in field_names:
            object_pointer = object
            model_pointer = object._meta.model
            path = field_name.split(".")
            for i, p in enumerate(path):
                if i < len(path) - 1:
                    # Dive into the nested object
                    object_pointer = getattr(object_pointer, p)
                    model_pointer = model_pointer._meta.get_field(p).remote_field.model
                else:
                    # We are at the end of the path, which is the field
                    field = model_pointer._meta.get_field(p)
                    value = getattr(object_pointer, p, None)
                    fields_and_values.append((field, self._get_field_value(field, value, replace_values)))

        return fields_and_values

    @staticmethod
    def _get_field_value(field, value, replace_values):
        if replace_values and field.name in replace_values:
            return replace_values[field.name]
        return value


@method_decorator(xframe_options_exempt, name="dispatch")
class TrafficSignPlanEmbed(TrafficSignEmbedMixin, DetailView):
    model = TrafficSignPlan
    mount_model = MountPlan
    mount_field_name = "mount_plan"
    traffic_sign_select_related: list[str] = [
        *_BASE_SIGN_SELECT_RELATED,
        "mount_plan__mount_type",
        "plan",
    ]
    additional_sign_select_related: list[str] = [
        *_COMMON_ADDITIONAL_SIGN_SELECT_RELATED,
        "mount_plan__mount_type",
        "plan",
    ]

    traffic_sign_fields: list[str] = [
        *_DEVICE_TYPE_FIELDS,
        "id",
        "lifecycle",
        #
        *_SIGN_LOCATION_FIELDS,
        #
        "value",
        *_VALIDITY_PERIOD_FIELDS,
        #
        "owner",
        "mount_type",
        #
        "txt",
        "plan",
        #
        *_SIGN_SOURCE_FIELDS,
    ]

    additional_sign_fields: list[str] = [
        *_DEVICE_TYPE_FIELDS,
        "id",
        "lifecycle",
        #
        *_SIGN_LOCATION_FIELDS,
        "color",
        #
        "content_s",
        *_VALIDITY_PERIOD_FIELDS,
        "additional_information",
        #
        "owner",
        "mount_type",
        #
        "parent",
        "mount_plan",
        "plan",
        #
        *_SIGN_SOURCE_FIELDS,
    ]

    mount_fields: list[str] = [
        *_MOUNT_TYPE_FIELDS,
        "id",
        "lifecycle",
        #
        *_MOUNT_PHYSICAL_FIELDS,
        #
        "owner",
        "electric_accountable",
        #
        "txt",
        #
        *_MOUNT_SOURCE_FIELDS,
    ]


@method_decorator(xframe_options_exempt, name="dispatch")
class TrafficSignRealEmbed(TrafficSignEmbedMixin, DetailView):
    model = TrafficSignReal
    mount_model = MountReal
    mount_field_name = "mount_real"
    traffic_sign_select_related: list[str] = [
        *_BASE_SIGN_SELECT_RELATED,
        "mount_real__mount_type",
        "mount_real__mount_plan__mount_type",
        "traffic_sign_plan",
    ]
    additional_sign_select_related: list[str] = [
        *_COMMON_ADDITIONAL_SIGN_SELECT_RELATED,
        "mount_real__mount_type",
        "additional_sign_plan",
    ]

    traffic_sign_fields: list[str] = [
        *_DEVICE_TYPE_FIELDS,
        "id",
        "lifecycle",
        "legacy_code",
        "traffic_sign_plan",
        #
        *_SIGN_LOCATION_FIELDS,
        #
        "value",
        *_VALIDITY_PERIOD_FIELDS,
        #
        *_INSTALLED_DEVICE_FIELDS_BASE,
        *_INSTALLED_DEVICE_FIELDS_SUFFIX,
        #
        "owner",
        "mount_type",
        #
        "txt",
        #
        *_SIGN_SOURCE_FIELDS,
    ]

    additional_sign_fields: list[str] = [
        *_DEVICE_TYPE_FIELDS,
        "id",
        "lifecycle",
        "additional_sign_plan",
        "legacy_code",
        #
        *_SIGN_LOCATION_FIELDS,
        "color",
        #
        "content_s",
        *_VALIDITY_PERIOD_FIELDS,
        #
        *_INSTALLED_DEVICE_FIELDS_BASE,
        "installed_by",
        *_INSTALLED_DEVICE_FIELDS_SUFFIX,
        #
        "owner",
        "mount_type",
        #
        "parent",
        "mount_real",
        #
        *_SIGN_SOURCE_FIELDS,
    ]

    mount_fields: list[str] = [
        *_MOUNT_TYPE_FIELDS,
        "id",
        "lifecycle",
        "mount_plan",
        #
        *_MOUNT_PHYSICAL_FIELDS,
        #
        "condition",
        "installation_date",
        "installation_status",
        "inspected_at",
        "diameter",
        #
        "owner",
        "electric_accountable",
        #
        "txt",
        #
        *_MOUNT_SOURCE_FIELDS,
    ]
