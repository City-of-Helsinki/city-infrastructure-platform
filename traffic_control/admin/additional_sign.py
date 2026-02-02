from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter
from guardian.admin import GuardedModelAdmin

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
)
from traffic_control.enums import Condition, InstallationStatus, LaneNumber, LaneType, Reflection, Size, Surface
from traffic_control.forms import (
    AdditionalSignPlanModelForm,
    AdditionalSignRealModelForm,
    AdminFileWidgetWithProxy,
    CityInfraFileUploadFormset,
)
from traffic_control.mixins import (
    DeviceTypeSearchAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    FormattedContentsAdminMixin,
    Geometry3DFieldAdminMixin,
    PreviewDeviceTypeRelationMixin,
    SoftDeleteAdminMixin,
    UpdatePlanLocationAdminMixin,
    UploadsFileProxyMixin,
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


class BaseAdditionalSignInline(admin.TabularInline, PreviewDeviceTypeRelationMixin, FormattedContentsAdminMixin):
    model = None
    fields = (
        "id",
        "device_type_preview",
        "content",
        "additional_information",
    )
    readonly_fields = (
        "id",
        "device_type_preview",
        "content",
        "additional_information",
    )
    extra = 0
    ordering = ("height",)
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent changes to related objects."""
        return False

    def save_model(self, request, obj, form, change):
        """Override to prevent saving."""
        pass

    def save_formset(self, request, form, formset, change):
        """Override to prevent saving formset."""
        pass


class AdditionalSignRealInline(BaseAdditionalSignInline):
    model = AdditionalSignReal
    verbose_name = _("Additional Sign Real")
    verbose_name_plural = _("Additional Sign Reals")


@admin.register(AdditionalSignPlanFile)
class AdditionalSignPlanFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file_proxy", "is_public")
    raw_id_fields = ("additional_sign_plan",)


@admin.register(AdditionalSignRealFile)
class AdditionalSignRealFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file_proxy", "is_public")
    raw_id_fields = ("additional_sign_real",)


class AdditionalSignPlanFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    model = AdditionalSignPlanFile
    formset = CityInfraFileUploadFormset


class AdditionalSignRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
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
    PreviewDeviceTypeRelationMixin,
    FormattedContentsAdminMixin,
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
                    "device_type",
                    "device_type_preview",
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
                    "location",
                    "z_coord",
                    "location_ewkt",
                    "direction",
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
                    "seasonal_validity_period_information",
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
        "device_type_preview",
        "content",
        "additional_information",
        "is_replaced_as_str",
    )
    readonly_fields = (
        "device_type_preview",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    raw_id_fields = ("parent", "plan", "mount_plan")

    list_filter = SoftDeleteAdminMixin.list_filter + [
        ("lifecycle", EnumFieldListFilter),
        "owner",
        AdditionalSignReplacementListFilter,
    ]
    search_fields = ("id",)
    ordering = ("-created_at",)
    inlines = (
        AdditionalSignPlanFileInline,
        AdditionalSignRealInline,
        AdditionalSignPlanReplacesInline,
        AdditionalSignPlanReplacedByInline,
    )
    initial_values = shared_initial_values

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs.prefetch_related("device_type")
            .prefetch_related("device_type__icon_file")
            .prefetch_related("replacement_to_new")
        )


@admin.register(AdditionalSignReal)
class AdditionalSignRealAdmin(
    DeviceTypeSearchAdminMixin,
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
    PreviewDeviceTypeRelationMixin,
    FormattedContentsAdminMixin,
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
                    "device_type",
                    "device_type_preview",
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
                    "location",
                    "z_coord",
                    "location_ewkt",
                    "direction",
                    "road_name",
                    "lane_number",
                    "lane_type",
                    "location_specifier",
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
                    "seasonal_validity_period_information",
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
        "device_type_preview",
        "content",
        "additional_information",
    )
    readonly_fields = (
        "device_type_preview",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    raw_id_fields = ("parent", "additional_sign_plan", "mount_real")
    ordering = ("-created_at",)
    list_filter = SoftDeleteAdminMixin.list_filter + [
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
        "id",
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
        return qs.select_related(
            "device_type",
            "device_type__icon_file",
            "created_by",
            "updated_by",
            "owner",
            "additional_sign_plan",
            "mount_real",
            # NOTE (2025-12-09 thiago)
            # Both mount_real__mount_type and mount_type need to be prefetched independently, since we have visible
            # columns that access the "mount_type.__str__" through different routes. Removing either prefetch will
            # drastically increase the query count
            "mount_real__mount_type",
            "mount_type",
        )


class AdditionalSignPlanInline(BaseAdditionalSignInline):
    model = AdditionalSignPlan
    verbose_name = _("Additional Sign Plan")
    verbose_name_plural = _("Additional Sign Plans")
