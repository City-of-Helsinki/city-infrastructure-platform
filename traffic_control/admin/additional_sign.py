from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter

from traffic_control.admin.audit_log import AuditLogHistoryAdmin
from traffic_control.admin.common import (
    OperationalAreaListFilter,
    PlanReplacementListFilterMixin,
    ReplacedByInline,
    ReplacesInline,
    TrafficControlOperationInlineBase,
)
from traffic_control.admin.utils import (
    AdminFieldInitialValuesMixin,
    DeviceComparisonAdminMixin,
    MultiResourceExportActionAdminMixin,
    ResponsibleEntityPermissionAdminMixin,
    ResponsibleEntityPermissionFilter,
    TreeModelFieldListFilter,
)
from traffic_control.enums import Condition, InstallationStatus, LaneNumber, LaneType, Reflection, Size, Surface
from traffic_control.forms import (
    AdditionalSignPlanModelForm,
    AdditionalSignRealModelForm,
    AdminFileWidget,
    CityInfraFileUploadFormset,
)
from traffic_control.mixins import (
    DeviceTypeSearchAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    Geometry3DFieldAdminMixin,
    SoftDeleteAdminMixin,
    UpdatePlanLocationAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
)
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignPlanFile,
    AdditionalSignReal,
    AdditionalSignRealFile,
)
from traffic_control.models.additional_sign import (
    AdditionalSignPlanReplacement,
    AdditionalSignRealOperation,
    Color,
)
from traffic_control.models.traffic_sign import LocationSpecifier
from traffic_control.resources.additional_sign import (
    AdditionalSignPlanResource,
    AdditionalSignPlanToRealTemplateResource,
    AdditionalSignRealResource,
)
from traffic_control.resources.common import CustomImportExportActionModelAdmin

shared_initial_values = {
    "size": Size.MEDIUM,
    "reflection_class": Reflection.R1,
    "surface_class": Surface.FLAT,
    "color": Color.BLUE,
    "lane_number": LaneNumber.MAIN_1,
    "lane_type": LaneType.MAIN,
    "location_specifier": LocationSpecifier.RIGHT,
}


class AdditionalSignPlanFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = AdditionalSignPlanFile
    formset = CityInfraFileUploadFormset


class AdditionalSignRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = AdditionalSignRealFile
    formset = CityInfraFileUploadFormset


class AdditionalSignRealOperationInline(TrafficControlOperationInlineBase):
    model = AdditionalSignRealOperation


class AdditionalSignPlanReplacesInline(ReplacesInline):
    model = AdditionalSignPlanReplacement


class AdditionalSignPlanReplacedByInline(ReplacedByInline):
    model = AdditionalSignPlanReplacement


class AdditionalSignReplacementListFilter(PlanReplacementListFilterMixin, SimpleListFilter):
    plan_model = AdditionalSignPlan


@admin.register(AdditionalSignPlan)
class AdditionalSignPlanAdmin(
    DeviceTypeSearchAdminMixin,
    ResponsibleEntityPermissionAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
    Geometry3DFieldAdminMixin,
    MultiResourceExportActionAdminMixin,
    AdminFieldInitialValuesMixin,
    UpdatePlanLocationAdminMixin,
    admin.GISModelAdmin,
    AuditLogHistoryAdmin,
    CustomImportExportActionModelAdmin,
):
    resource_class = AdditionalSignPlanResource
    extra_export_resource_classes = [AdditionalSignPlanToRealTemplateResource]
    form = AdditionalSignPlanModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "responsible_entity",
                    "device_type",
                    "content_s",
                    "missing_content",
                    "additional_information",
                    "mount_type",
                    "source_id",
                    "source_name",
                )
            },
        ),
        (
            _("Location information"),
            {
                "fields": (
                    ("location", "z_coord", "location_ewkt"),
                    "direction",
                    "order",
                    "road_name",
                    "lane_number",
                    "lane_type",
                    "location_specifier",
                )
            },
        ),
        (
            _("Physical properties"),
            {"fields": ("size", "height", "color", "reflection_class", "surface_class")},
        ),
        (_("Related models"), {"fields": ("parent", "plan", "mount_plan")}),
        (
            _("Validity"),
            {
                "fields": (
                    ("validity_period_start", "validity_period_end"),
                    ("seasonal_validity_period_start", "seasonal_validity_period_end"),
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
        "device_type",
        "lifecycle",
        "location",
        "is_replaced_as_str",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    raw_id_fields = ("parent", "plan", "mount_plan")

    list_filter = SoftDeleteAdminMixin.list_filter + [
        ResponsibleEntityPermissionFilter,
        ("responsible_entity", TreeModelFieldListFilter),
        ("lifecycle", EnumFieldListFilter),
        "owner",
        AdditionalSignReplacementListFilter,
    ]
    ordering = ("-created_at",)
    inlines = (
        AdditionalSignPlanFileInline,
        AdditionalSignPlanReplacesInline,
        AdditionalSignPlanReplacedByInline,
    )
    initial_values = shared_initial_values

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("device_type")


@admin.register(AdditionalSignReal)
class AdditionalSignRealAdmin(
    DeviceTypeSearchAdminMixin,
    ResponsibleEntityPermissionAdminMixin,
    DeviceComparisonAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
    Geometry3DFieldAdminMixin,
    AdminFieldInitialValuesMixin,
    admin.GISModelAdmin,
    AuditLogHistoryAdmin,
    CustomImportExportActionModelAdmin,
):
    plan_model_field_name = "additional_sign_plan"
    resource_class = AdditionalSignRealResource
    form = AdditionalSignRealModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "responsible_entity",
                    "device_type",
                    "content_s",
                    "missing_content",
                    "additional_information",
                    "mount_type",
                    "permit_decision_id",
                    "attachment_url",
                    "scanned_at",
                    "operation",
                    "manufacturer",
                    "rfid",
                    "legacy_code",
                    "source_id",
                    "source_name",
                )
            },
        ),
        (
            _("Location information"),
            {
                "fields": (
                    ("location", "z_coord", "location_ewkt"),
                    "direction",
                    "order",
                    "road_name",
                    "lane_number",
                    "lane_type",
                    "location_specifier",
                    "coverage_area",
                )
            },
        ),
        (
            _("Physical properties"),
            {
                "fields": (
                    "size",
                    "height",
                    "color",
                    "reflection_class",
                    "surface_class",
                    "condition",
                )
            },
        ),
        (
            _("Related models"),
            {"fields": ("parent", "additional_sign_plan", "mount_real")},
        ),
        (
            _("Installation information"),
            {
                "fields": (
                    "installation_id",
                    "installation_details",
                    "installation_date",
                    "installation_status",
                    "installed_by",
                )
            },
        ),
        (
            _("Validity"),
            {
                "fields": (
                    ("validity_period_start", "validity_period_end"),
                    ("seasonal_validity_period_start", "seasonal_validity_period_end"),
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
        "device_type",
        "additional_sign_plan",
        "legacy_code",
        "installation_id",
        "installation_details",
        "installation_date",
        "size",
        "mount_real",
        "mount_type",
        "height",
        "installation_status",
        "validity_period_start",
        "validity_period_end",
        "condition",
        "reflection_class",
        "surface_class",
        "seasonal_validity_period_start",
        "seasonal_validity_period_end",
        "owner",
        "lifecycle",
        "road_name",
        "lane_number",
        "lane_type",
        "location_specifier",
        "rfid",
        "direction",
        "operation",
        "manufacturer",
        "permit_decision_id",
        "color",
        "attachment_url",
        "scanned_at",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "source_id",
        "source_name",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    raw_id_fields = ("parent", "additional_sign_plan", "mount_real")
    ordering = ("-created_at",)
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ResponsibleEntityPermissionFilter,
        ("responsible_entity", TreeModelFieldListFilter),
        ("lifecycle", EnumFieldListFilter),
        ("installation_status", EnumFieldListFilter),
        ("condition", EnumFieldListFilter),
        ("reflection_class", EnumFieldListFilter),
        ("surface_class", EnumFieldListFilter),
        ("location_specifier", EnumFieldListFilter),
        ("color", EnumFieldListFilter),
        "owner",
        OperationalAreaListFilter,
    ]
    search_fields = (
        "size",
        "height",
        "reflection_class",
        "surface_class",
        "road_name",
        "lane_number",
        "lane_type",
        "source_id",
        "source_name",
    )
    inlines = (
        AdditionalSignRealFileInline,
        AdditionalSignRealOperationInline,
    )
    initial_values = {
        **shared_initial_values,
        "condition": Condition.VERY_GOOD,
        "installation_status": InstallationStatus.IN_USE,
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs.prefetch_related("device_type")
            .prefetch_related("created_by")
            .prefetch_related("updated_by")
            .prefetch_related("additional_sign_plan")
            .prefetch_related("mount_real")
            .prefetch_related("mount_type")
        )


class BaseAdditionalSignInline(admin.TabularInline):
    model = None
    fields = (
        "order",
        "id",
        "device_type",
        "content_s",
    )
    readonly_fields = (
        "id",
        "device_type",
        "content_s",
    )
    extra = 0
    ordering = ("order",)
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


class AdditionalSignPlanInline(BaseAdditionalSignInline):
    model = AdditionalSignPlan
    verbose_name = _("Additional Sign Plan")
    verbose_name_plural = _("Additional Sign Plans")


class AdditionalSignRealInline(BaseAdditionalSignInline):
    model = AdditionalSignReal
    verbose_name = _("Additional Sign Real")
    verbose_name_plural = _("Additional Sign Reals")
