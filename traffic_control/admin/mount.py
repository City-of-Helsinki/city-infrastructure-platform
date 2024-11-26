from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter

from traffic_control.admin.audit_log import AuditLogHistoryAdmin
from traffic_control.admin.common import (
    PlanReplacementListFilterMixin,
    ReplacedByInline,
    ReplacesInline,
    TrafficControlOperationInlineBase,
)
from traffic_control.admin.traffic_sign import OrderedTrafficSignRealInline
from traffic_control.admin.utils import (
    AdminFieldInitialValuesMixin,
    DeviceComparisonAdminMixin,
    MultiResourceExportActionAdminMixin,
    ResponsibleEntityPermissionAdminMixin,
    ResponsibleEntityPermissionFilter,
    TreeModelFieldListFilter,
)
from traffic_control.constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from traffic_control.enums import Condition, InstallationStatus
from traffic_control.forms import AdminFileWidget, CityInfraFileUploadFormset, MountPlanModelForm, MountRealModelForm
from traffic_control.mixins import (
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UpdatePlanLocationAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
)
from traffic_control.models import (
    MountPlan,
    MountPlanFile,
    MountPlanReplacement,
    MountReal,
    MountRealFile,
    MountType,
    PortalType,
)
from traffic_control.resources.common import CustomImportExportActionModelAdmin
from traffic_control.resources.mount import MountPlanResource, MountPlanToRealTemplateResource, MountRealResource

__all__ = (
    "MountPlanAdmin",
    "MountPlanFileInline",
    "MountRealAdmin",
    "MountRealFileInline",
    "PortalTypeAdmin",
)

from traffic_control.models.mount import MountRealOperation


class MountPlanFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = MountPlanFile
    formset = CityInfraFileUploadFormset


class MountPlanReplacesInline(ReplacesInline):
    model = MountPlanReplacement


class MountPlanReplacedByInline(ReplacedByInline):
    model = MountPlanReplacement


class MountPlanReplacementListFilter(PlanReplacementListFilterMixin, SimpleListFilter):
    plan_model = MountPlan


@admin.register(MountPlan)
class MountPlanAdmin(
    ResponsibleEntityPermissionAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    MultiResourceExportActionAdminMixin,
    AdminFieldInitialValuesMixin,
    UpdatePlanLocationAdminMixin,
    admin.GISModelAdmin,
    AuditLogHistoryAdmin,
    CustomImportExportActionModelAdmin,
):
    resource_class = MountPlanResource
    extra_export_resource_classes = [MountPlanToRealTemplateResource]
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    form = MountPlanModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "responsible_entity",
                    "electric_accountable",
                    "txt",
                    "source_id",
                    "source_name",
                )
            },
        ),
        (_("Location information"), {"fields": ("location", "road_name", "location_specifier")}),
        (
            _("Physical properties"),
            {
                "fields": (
                    "mount_type",
                    "portal_type",
                    "base",
                    "material",
                    "height",
                    "cross_bar_length",
                    "is_foldable",
                )
            },
        ),
        (_("Related models"), {"fields": ("plan",)}),
        (
            _("Validity"),
            {
                "fields": (
                    ("validity_period_start", "validity_period_end"),
                    "lifecycle",
                )
            },
        ),
        (
            _("Metadata"),
            {"fields": ("created_at", "updated_at", "created_by", "updated_by")},
        ),
    )
    list_display = (
        "id",
        "mount_type",
        "lifecycle",
        "location",
        "is_replaced_as_str",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ResponsibleEntityPermissionFilter,
        ("responsible_entity", TreeModelFieldListFilter),
        ("lifecycle", EnumFieldListFilter),
        "owner",
        MountPlanReplacementListFilter,
    ]
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "source_name",
        "source_id",
    )
    raw_id_fields = ("plan",)
    ordering = ("-created_at",)
    inlines = (
        MountPlanFileInline,
        MountPlanReplacesInline,
        MountPlanReplacedByInline,
    )
    initial_values = {}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("mount_type")


class MountRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = MountRealFile
    formset = CityInfraFileUploadFormset


class MountRealOperationInline(TrafficControlOperationInlineBase):
    model = MountRealOperation


@admin.register(MountReal)
class MountRealAdmin(
    DeviceComparisonAdminMixin,
    ResponsibleEntityPermissionAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
    AdminFieldInitialValuesMixin,
    admin.GISModelAdmin,
    AuditLogHistoryAdmin,
    CustomImportExportActionModelAdmin,
):
    plan_model_field_name = "mount_plan"
    resource_class = MountRealResource
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    form = MountRealModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "responsible_entity",
                    "electric_accountable",
                    "inspected_at",
                    "txt",
                    "source_id",
                    "source_name",
                    "attachment_url",
                )
            },
        ),
        (_("Location information"), {"fields": ("location",)}),
        (
            _("Physical properties"),
            {
                "fields": (
                    "mount_type",
                    "portal_type",
                    "base",
                    "material",
                    "height",
                    "cross_bar_length",
                    "diameter",
                    "is_foldable",
                    "condition",
                )
            },
        ),
        (_("Related models"), {"fields": ("mount_plan",)}),
        (
            _("Installation information"),
            {"fields": ("installation_date", "installation_status")},
        ),
        (
            _("Validity"),
            {
                "fields": (
                    ("validity_period_start", "validity_period_end"),
                    "lifecycle",
                )
            },
        ),
        (
            _("Metadata"),
            {"fields": ("created_at", "updated_at", "created_by", "updated_by")},
        ),
    )
    list_display = (
        "id",
        "mount_type",
        "lifecycle",
        "location",
        "attachment_url",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ResponsibleEntityPermissionFilter,
        ("responsible_entity", TreeModelFieldListFilter),
        ("lifecycle", EnumFieldListFilter),
        "owner",
    ]
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "source_name",
        "source_id",
    )
    raw_id_fields = ("mount_plan",)
    ordering = ("-created_at",)
    inlines = (
        MountRealFileInline,
        OrderedTrafficSignRealInline,
        MountRealOperationInline,
    )
    initial_values = {
        "installation_status": InstallationStatus.IN_USE,
        "condition": Condition.VERY_GOOD,
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("mount_type")


@admin.register(MountType)
class MountTypeAdmin(AuditLogHistoryAdmin):
    list_display = (
        "code",
        "description",
        "description_fi",
        "digiroad_code",
        "digiroad_description",
    )
    ordering = ("code", "description")


@admin.register(PortalType)
class PortalTypeAdmin(AuditLogHistoryAdmin):
    list_display = (
        "structure",
        "build_type",
        "model",
    )
    ordering = ("structure", "build_type", "model")
    actions = None
