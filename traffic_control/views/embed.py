from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView

from traffic_control.models import MountPlan, MountReal, TrafficSignPlan, TrafficSignReal


@method_decorator(xframe_options_exempt, name="dispatch")
class TrafficSignEmbed(DetailView):
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
        return (
            super()
            .get_queryset()
            .active()
            .select_related(
                "device_type",
                "mount_type",
                "owner",
                "responsible_entity",
            )
        )

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
            .order_by("order")
            .select_related("device_type", "owner", "responsible_entity")
        )

        additional_signs = []
        for object in objects:
            additional_signs.append(
                {
                    "fields": self.get_fields_and_values(object, self.additional_sign_fields),
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

    def get_fields_and_values(self, object, field_names):
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
                    fields_and_values.append((field, value))

        return fields_and_values


class TrafficSignPlanEmbed(TrafficSignEmbed):
    model = TrafficSignPlan
    mount_model = MountPlan
    mount_field_name = "mount_plan"

    traffic_sign_fields = [
        "device_type.code",
        "device_type.description",
        "device_type.legacy_code",
        "id",
        "lifecycle",
        #
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
        #
        "value",
        "validity_period_start",
        "validity_period_end",
        "seasonal_validity_period_start",
        "seasonal_validity_period_end",
        #
        "owner",
        "responsible_entity",
        "mount_type",
        #
        "txt",
        "plan",
        #
        "created_at",
        "updated_at",
        "source_id",
        "source_name",
    ]

    additional_sign_fields = [
        "device_type.code",
        "device_type.description",
        "device_type.legacy_code",
        "id",
        "lifecycle",
        #
        "location",
        "order",
        "road_name",
        "lane_number",
        "lane_type",
        "direction",
        "location_specifier",
        "height",
        "size",
        "reflection_class",
        "surface_class",
        "color",
        #
        "content_s",
        "validity_period_start",
        "validity_period_end",
        "seasonal_validity_period_start",
        "seasonal_validity_period_end",
        #
        "owner",
        "responsible_entity",
        "mount_type",
        #
        "parent",
        "mount_plan",
        "plan",
        #
        "created_at",
        "updated_at",
        "source_id",
        "source_name",
    ]

    mount_fields = [
        "mount_type.code",
        "mount_type.description",
        "mount_type.description_fi",
        "mount_type.digiroad_code",
        "mount_type.digiroad_description",
        "id",
        "lifecycle",
        #
        "location",
        "height",
        "cross_bar_length",
        "base",
        "portal_type",
        "material",
        "is_foldable",
        "validity_period_start",
        "validity_period_end",
        #
        "owner",
        "responsible_entity",
        "electric_accountable",
        #
        "txt",
        #
        "created_at",
        "updated_at",
        "source_name",
        "source_id",
    ]


class TrafficSignRealEmbed(TrafficSignEmbed):
    model = TrafficSignReal
    mount_model = MountReal
    mount_field_name = "mount_real"

    traffic_sign_fields = [
        "device_type.code",
        "device_type.description",
        "device_type.legacy_code",
        "id",
        "lifecycle",
        "legacy_code",
        "traffic_sign_plan",
        #
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
        #
        "value",
        "validity_period_start",
        "validity_period_end",
        "seasonal_validity_period_start",
        "seasonal_validity_period_end",
        #
        "condition",
        "installation_date",
        "installation_status",
        "installation_id",
        "installation_details",
        "permit_decision_id",
        "scanned_at",
        "manufacturer",
        "rfid",
        "operation",
        "attachment_url",
        #
        "owner",
        "responsible_entity",
        "mount_type",
        #
        "txt",
        #
        "created_at",
        "updated_at",
        "source_id",
        "source_name",
    ]

    additional_sign_fields = [
        "device_type.code",
        "device_type.description",
        "device_type.legacy_code",
        "id",
        "lifecycle",
        "additional_sign_plan",
        "legacy_code",
        #
        "location",
        "order",
        "road_name",
        "lane_number",
        "lane_type",
        "direction",
        "location_specifier",
        "height",
        "size",
        "reflection_class",
        "surface_class",
        "color",
        #
        "content_s",
        "validity_period_start",
        "validity_period_end",
        "seasonal_validity_period_start",
        "seasonal_validity_period_end",
        #
        "condition",
        "installation_date",
        "installation_status",
        "installation_id",
        "installation_details",
        "installed_by",
        "permit_decision_id",
        "scanned_at",
        "manufacturer",
        "rfid",
        "operation",
        "attachment_url",
        #
        "owner",
        "responsible_entity",
        "mount_type",
        #
        "parent",
        "mount_real",
        #
        "created_at",
        "updated_at",
        "source_id",
        "source_name",
    ]

    mount_fields = [
        "mount_type.code",
        "mount_type.description",
        "mount_type.description_fi",
        "mount_type.digiroad_code",
        "mount_type.digiroad_description",
        "id",
        "lifecycle",
        "mount_plan",
        #
        "location",
        "height",
        "cross_bar_length",
        "base",
        "portal_type",
        "material",
        "is_foldable",
        "validity_period_start",
        "validity_period_end",
        #
        "condition",
        "installation_date",
        "installation_status",
        "inspected_at",
        "diameter",
        #
        "owner",
        "responsible_entity",
        "electric_accountable",
        #
        "txt",
        #
        "created_at",
        "updated_at",
        "source_name",
        "source_id",
    ]
