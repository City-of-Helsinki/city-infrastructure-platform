from django.db.models import Prefetch, QuerySet
from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView

from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    MountPlan,
    MountReal,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.models.utils import order_queryset_by_z_coord_desc

# ---------------------------------------------------------------------------
# Shared select_related fragments
# ---------------------------------------------------------------------------

_BASE_SIGN_SELECT_RELATED: list[str] = [
    "device_type",
    "device_type__icon_file",
    "mount_type",
    "owner",
]

_COMMON_ADDITIONAL_SIGN_SELECT_RELATED: list[str] = [
    *_BASE_SIGN_SELECT_RELATED,
    "parent",
    # The parent is rendered through its __str__, which reads its device type.
    "parent__device_type",
]

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

# ---------------------------------------------------------------------------
# Shared field lists
#
# These are shared by the traffic sign pages and the dedicated additional sign and mount pages, so
# that every page shows the same information for a given kind of object. Changing a list here
# changes it on every page that shows that object.
# ---------------------------------------------------------------------------

_TRAFFIC_SIGN_PLAN_FIELDS: list[str] = [
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

_TRAFFIC_SIGN_REAL_FIELDS: list[str] = [
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

_ADDITIONAL_SIGN_PLAN_FIELDS: list[str] = [
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

_ADDITIONAL_SIGN_REAL_FIELDS: list[str] = [
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

_MOUNT_PLAN_FIELDS: list[str] = [
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

_MOUNT_REAL_FIELDS: list[str] = [
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


def build_additional_sign_context(view, additional_sign, field_names: list[str]) -> dict:
    """Build the context of a single additional sign shown as part of another object's page.

    `content_s` is replaced by its rendered rows, as the raw JSON value is not readable.

    Args:
        view: View resolving the field values.
        additional_sign: Additional sign plan or real to describe.
        field_names (list[str]): Fields to show for the additional sign.

    Returns:
        dict: The additional sign itself under "object" and its fields under "fields".
    """
    return {
        "fields": view.get_fields_and_values(
            additional_sign,
            field_names,
            {"content_s": additional_sign.get_content_s_rows()},
        ),
        "object": additional_sign,
    }


class BaseEmbedMixin:
    """Shared plumbing for the embedded detail pages.

    Subclasses provide the template, the field lists and the extra context their page needs. This
    class only handles fetching the object, resolving field values and reporting a missing object
    in a way that is readable inside an iframe.
    """

    @property
    def title(self) -> str:
        """Page title shown in the browser or iframe.

        Returns:
            str: Verbose name and id of the object, extended by subclasses.
        """
        return f"{self.model._meta.verbose_name} {self.object.id}"

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            return self.handle_404(request, *args, **kwargs)

    def handle_404(self, request, *args, **kwargs) -> HttpResponse:
        """Report a missing object as plain text instead of an HTML error page.

        Args:
            request: The current request.
            *args: Positional arguments of the view.
            **kwargs: Keyword arguments of the view, including the requested "pk".

        Returns:
            HttpResponse: Plain text 404 response naming the model and the id.
        """
        model_name = self.model._meta.verbose_name
        object_id = kwargs.get("pk")
        return HttpResponse(
            _("Error: Could not find %(model_name)s with id %(id)s.") % {"model_name": model_name, "id": object_id},
            content_type="text/plain;charset=utf-8",
            status=404,
        )

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "title": self.title}

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


class DeviceTypeTitleMixin:
    """Title that names the device type of the object, for pages that show a single device."""

    @property
    def title(self) -> str:
        """Page title naming the object and its device type.

        Returns:
            str: Verbose name and id of the object, followed by the device type when it has one.
        """
        title = super().title
        device_type = self.object.device_type
        if device_type:
            title += f" - {device_type.code} {device_type.description}"
        return title


class TrafficSignEmbedMixin(DeviceTypeTitleMixin, BaseEmbedMixin):
    template_name = "embed/traffic_sign.html"

    def get_queryset(self):
        return super().get_queryset().active().select_related(*self.traffic_sign_select_related)

    def get_context_data(self, **kwargs):
        parent_context = super().get_context_data(**kwargs)
        traffic_sign = parent_context["object"]
        return {
            **parent_context,
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
        return [build_additional_sign_context(self, object, self.additional_sign_fields) for object in objects]

    def get_mount_fields(self, object):
        mount = getattr(object, self.mount_field_name)

        if mount:
            return self.get_fields_and_values(mount, self.mount_fields)
        else:
            return []


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

    traffic_sign_fields: list[str] = _TRAFFIC_SIGN_PLAN_FIELDS
    additional_sign_fields: list[str] = _ADDITIONAL_SIGN_PLAN_FIELDS
    mount_fields: list[str] = _MOUNT_PLAN_FIELDS


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

    traffic_sign_fields: list[str] = _TRAFFIC_SIGN_REAL_FIELDS
    additional_sign_fields: list[str] = _ADDITIONAL_SIGN_REAL_FIELDS
    mount_fields: list[str] = _MOUNT_REAL_FIELDS


class AdditionalSignEmbedMixin(DeviceTypeTitleMixin, BaseEmbedMixin):
    """Page of a single additional sign, showing the same information as the traffic sign page."""

    template_name = "embed/additional_sign.html"

    def get_queryset(self) -> QuerySet:
        """Limit the page to additional signs that are in use.

        Returns:
            QuerySet: Active additional signs with the related objects the page needs.
        """
        return super().get_queryset().active().select_related(*self.additional_sign_select_related)

    def get_context_data(self, **kwargs) -> dict:
        parent_context = super().get_context_data(**kwargs)
        additional_sign = parent_context["object"]
        return {
            **parent_context,
            "additional_sign_fields": self.get_fields_and_values(
                additional_sign,
                self.additional_sign_fields,
                {"content_s": additional_sign.get_content_s_rows()},
            ),
        }


@method_decorator(xframe_options_exempt, name="dispatch")
class AdditionalSignPlanEmbed(AdditionalSignEmbedMixin, DetailView):
    model = AdditionalSignPlan
    additional_sign_select_related: list[str] = [
        *_COMMON_ADDITIONAL_SIGN_SELECT_RELATED,
        "mount_plan__mount_type",
        "plan",
    ]
    additional_sign_fields: list[str] = _ADDITIONAL_SIGN_PLAN_FIELDS


@method_decorator(xframe_options_exempt, name="dispatch")
class AdditionalSignRealEmbed(AdditionalSignEmbedMixin, DetailView):
    model = AdditionalSignReal
    additional_sign_select_related: list[str] = [
        *_COMMON_ADDITIONAL_SIGN_SELECT_RELATED,
        "mount_real__mount_type",
        "additional_sign_plan",
    ]
    additional_sign_fields: list[str] = _ADDITIONAL_SIGN_REAL_FIELDS


class MountEmbedMixin(BaseEmbedMixin):
    """Page of a single mount, showing every device attached to it.

    The visual section groups additional signs under their parent traffic sign, while the
    additional sign section lists every additional sign attached to the mount, including ones
    that have no parent traffic sign.
    """

    template_name = "embed/mount.html"

    @property
    def title(self) -> str:
        """Page title naming the mount and its mount type.

        Returns:
            str: Verbose name and id of the mount, followed by the mount type when it has one.
        """
        title = super().title
        mount_type = self.object.mount_type
        if mount_type:
            title += f" - {mount_type.code} {mount_type.description}"
        return title

    def get_queryset(self) -> QuerySet:
        """Limit the page to mounts that are in use.

        Returns:
            QuerySet: Active mounts with the related objects the page needs.
        """
        return super().get_queryset().active().select_related(*self.mount_select_related)

    def get_context_data(self, **kwargs) -> dict:
        parent_context = super().get_context_data(**kwargs)
        mount = parent_context["object"]
        traffic_signs = self.get_traffic_signs(mount)
        return {
            **parent_context,
            "mount_fields": self.get_fields_and_values(mount, self.mount_fields),
            "traffic_signs": traffic_signs,
            "additional_signs": self.get_additional_signs(mount),
        }

    def get_traffic_signs(self, mount) -> list[dict]:
        """Describe the traffic signs on the mount, each with its own additional signs.

        Args:
            mount: Mount plan or real the page is showing.

        Returns:
            list[dict]: Per traffic sign its object, its fields and its additional signs.
        """
        queryset = getattr(mount, self.traffic_sign_related_name).active()
        traffic_signs = (
            order_queryset_by_z_coord_desc(queryset)
            .select_related(*self.traffic_sign_select_related)
            .prefetch_related(
                Prefetch(
                    "additional_signs",
                    queryset=self.get_additional_sign_queryset(),
                    to_attr="embed_additional_signs",
                )
            )
        )
        return [
            {
                "object": traffic_sign,
                "fields": self.get_fields_and_values(traffic_sign, self.traffic_sign_fields),
                "additional_signs": self.get_child_additional_signs(traffic_sign),
            }
            for traffic_sign in traffic_signs
        ]

    def get_additional_sign_queryset(self) -> QuerySet:
        """Build the queryset used for every additional sign list on the page.

        Returns:
            QuerySet: Active additional signs, ordered from top down, with related objects.
        """
        return (
            self.additional_sign_model.objects.active()
            .order_by("-height")
            .select_related(*self.additional_sign_select_related)
        )

    def get_child_additional_signs(self, traffic_sign) -> list[dict]:
        """Describe the additional signs of a single traffic sign on the mount.

        Args:
            traffic_sign: Traffic sign plan or real on the mount.

        Returns:
            list[dict]: Per additional sign its object and its fields, ordered from top down.
        """
        return [
            build_additional_sign_context(self, object, self.additional_sign_fields)
            for object in traffic_sign.embed_additional_signs
        ]

    def get_additional_signs(self, mount) -> list[dict]:
        """Describe every additional sign attached to the mount.

        Additional signs are scoped by their mount, not by their parent traffic sign, so signs
        that have no parent are listed too.

        Args:
            mount: Mount plan or real the page is showing.

        Returns:
            list[dict]: Per additional sign its object and its fields, ordered from top down.
        """
        objects = (
            getattr(mount, self.additional_sign_related_name)
            .active()
            .order_by("-height")
            .select_related(*self.additional_sign_select_related)
        )
        return [build_additional_sign_context(self, object, self.additional_sign_fields) for object in objects]


@method_decorator(xframe_options_exempt, name="dispatch")
class MountPlanEmbed(MountEmbedMixin, DetailView):
    model = MountPlan
    traffic_sign_related_name = "trafficsignplan_set"
    additional_sign_related_name = "additionalsignplan_set"
    additional_sign_model = AdditionalSignPlan
    mount_select_related: list[str] = ["mount_type", "owner", "portal_type", "plan"]
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

    mount_fields: list[str] = _MOUNT_PLAN_FIELDS
    traffic_sign_fields: list[str] = _TRAFFIC_SIGN_PLAN_FIELDS
    additional_sign_fields: list[str] = _ADDITIONAL_SIGN_PLAN_FIELDS


@method_decorator(xframe_options_exempt, name="dispatch")
class MountRealEmbed(MountEmbedMixin, DetailView):
    model = MountReal
    traffic_sign_related_name = "trafficsignreal_set"
    additional_sign_related_name = "additionalsignreal_set"
    additional_sign_model = AdditionalSignReal
    mount_select_related: list[str] = ["mount_type", "owner", "portal_type", "mount_plan"]
    traffic_sign_select_related: list[str] = [
        *_BASE_SIGN_SELECT_RELATED,
        "mount_real__mount_type",
        "traffic_sign_plan",
    ]
    additional_sign_select_related: list[str] = [
        *_COMMON_ADDITIONAL_SIGN_SELECT_RELATED,
        "mount_real__mount_type",
        "additional_sign_plan",
    ]

    mount_fields: list[str] = _MOUNT_REAL_FIELDS
    traffic_sign_fields: list[str] = _TRAFFIC_SIGN_REAL_FIELDS
    additional_sign_fields: list[str] = _ADDITIONAL_SIGN_REAL_FIELDS
