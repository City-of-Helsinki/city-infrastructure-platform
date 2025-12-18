from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin
from django.db import models
from django.db.models import Exists, OuterRef
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter
from guardian.admin import GuardedModelAdmin

from traffic_control.admin.additional_sign import AdditionalSignPlanInline, AdditionalSignRealInline
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
from traffic_control.decorators import annotate_queryset
from traffic_control.enums import (
    Condition,
    InstallationStatus,
    LaneNumber,
    LaneType,
    Reflection,
    Size,
    Surface,
    TRAFFIC_SIGN_TYPE_CHOICES,
)
from traffic_control.forms import (
    AdminFileWidgetWithProxy,
    CityInfraFileUploadFormset,
    TrafficControlDeviceTypeForm,
    TrafficControlDeviceTypeIconForm,
    TrafficSignPlanModelForm,
    TrafficSignRealModelForm,
)
from traffic_control.mixins import (
    DeviceTypeSearchAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    Geometry3DFieldAdminMixin,
    PreviewDeviceTypeRelationMixin,
    PreviewIconFileRelationMixin,
    PreviewImageFileFieldMixin,
    SoftDeleteAdminMixin,
    UpdatePlanLocationAdminMixin,
    UploadsFileProxyMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
)
from traffic_control.models import (
    AdditionalSignPlan,
    TrafficControlDeviceType,
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignPlanReplacement,
    TrafficSignReal,
    TrafficSignRealFile,
)
from traffic_control.models.common import TrafficControlDeviceTypeIcon
from traffic_control.models.traffic_sign import LocationSpecifier, TrafficSignRealOperation
from traffic_control.models.utils import order_queryset_by_z_coord_desc
from traffic_control.resources.common import CustomImportExportActionModelAdmin
from traffic_control.resources.device_type import TrafficControlDeviceTypeResource
from traffic_control.resources.device_type_icon import (
    TrafficControlDeviceTypeIconResource,
)
from traffic_control.resources.traffic_sign import (
    TrafficSignPlanResource,
    TrafficSignPlanToRealTemplateResource,
    TrafficSignRealResource,
)

__all__ = (
    "OrderedTrafficSignRealInline",
    "TrafficControlDeviceTypeAdmin",
    "TrafficSignPlanAdmin",
    "TrafficSignPlanFileInline",
    "TrafficSignRealAdmin",
    "TrafficSignRealFileInline",
)

shared_initial_values = {
    "lane_number": LaneNumber.MAIN_1,
    "lane_type": LaneType.MAIN,
    "size": Size.MEDIUM,
    "reflection_class": Reflection.R1,
    "surface_class": Surface.FLAT,
    "location_specifier": LocationSpecifier.RIGHT,
}


@admin.register(TrafficSignPlanFile)
class TrafficSignPlanFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file_proxy", "is_public")
    raw_id_fields = ("traffic_sign_plan",)


@admin.register(TrafficSignRealFile)
class TrafficSignRealFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file_proxy", "is_public")
    raw_id_fields = ("traffic_sign_real",)


class TrafficSignTypeListFilter(SimpleListFilter):
    title = _("Traffic sign type")
    parameter_name = "traffic_sign_type"

    def lookups(self, request, model_admin):
        return TRAFFIC_SIGN_TYPE_CHOICES

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(code__startswith=value)
        return queryset


@admin.register(TrafficControlDeviceTypeIcon)
class TrafficControlDeviceTypeIconAdmin(CustomImportExportActionModelAdmin, PreviewImageFileFieldMixin):
    resource_class = TrafficControlDeviceTypeIconResource
    form = TrafficControlDeviceTypeIconForm
    list_display = ("id", "image_file_preview", "file")
    readonly_fields = ("image_file_preview",)
    search_fields = ("id", "file")


@admin.register(TrafficControlDeviceType)
class TrafficControlDeviceTypeAdmin(
    EnumChoiceValueDisplayAdminMixin,
    AuditLogHistoryAdmin,
    CustomImportExportActionModelAdmin,
    PreviewIconFileRelationMixin,
):
    form = TrafficControlDeviceTypeForm
    resource_class = TrafficControlDeviceTypeResource
    list_display = (
        "code",
        "icon_preview",
        "icon_file",
        "description",
        "value",
        "unit",
        "size",
        "legacy_code",
        "legacy_description",
        "target_model",
    )
    list_select_related = ("icon_file",)
    list_filter = (TrafficSignTypeListFilter,)
    search_fields = (
        "code",
        "legacy_code",
        "id",
        "description",
        "legacy_description",
    )
    search_help_text = "Searches from code and legacy_code fields"
    ordering = ("code",)
    actions = None


class TrafficSignPlanFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    model = TrafficSignPlanFile
    formset = CityInfraFileUploadFormset


class OrderedTrafficSignRealInline(admin.TabularInline):
    model = TrafficSignReal
    fields = ("id", "z_coord")
    readonly_fields = ("id", "z_coord")
    show_change_link = True
    can_delete = False
    verbose_name = _("Ordered traffic sign")
    verbose_name_plural = _("Ordered traffic signs")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return order_queryset_by_z_coord_desc(qs)

    def z_coord(self, obj):
        return obj.location.z

    z_coord.short_description = _("Location (z)")

    def has_add_permission(self, request, obj=None):
        return False


class TrafficSignPlanReplacesInline(ReplacesInline):
    model = TrafficSignPlanReplacement


class TrafficSignPlanReplacedByInline(ReplacedByInline):
    model = TrafficSignPlanReplacement


class TrafficSignPlanReplacementListFilter(PlanReplacementListFilterMixin, SimpleListFilter):
    plan_model = TrafficSignPlan


@admin.register(TrafficSignPlan)
class TrafficSignPlanAdmin(
    DeviceTypeSearchAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    Geometry3DFieldAdminMixin,
    MultiResourceExportActionAdminMixin,
    AdminFieldInitialValuesMixin,
    UpdatePlanLocationAdminMixin,
    admin.GISModelAdmin,
    AuditLogHistoryAdmin,
    CustomImportExportActionModelAdmin,
    PreviewDeviceTypeRelationMixin,
):
    resource_class = TrafficSignPlanResource
    extra_export_resource_classes = [TrafficSignPlanToRealTemplateResource]
    form = TrafficSignPlanModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "device_type",
                    "device_type_preview",
                    "mount_type",
                    "value",
                    "txt",
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
                    "reflection_class",
                    "surface_class",
                    "double_sided",
                    "peak_fastened",
                )
            },
        ),
        (_("Related models"), {"fields": ("plan", "mount_plan")}),
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
        "value",
        "lifecycle",
        "location",
        "has_additional_signs",
        "is_replaced_as_str",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ("lifecycle", EnumFieldListFilter),
        "owner",
        TrafficSignPlanReplacementListFilter,
    ]
    search_fields = ("id",)
    readonly_fields = (
        "device_type_preview",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    raw_id_fields = ("plan", "mount_plan")
    ordering = ("-created_at",)
    inlines = (
        TrafficSignPlanFileInline,
        AdditionalSignPlanInline,
        OrderedTrafficSignRealInline,
        TrafficSignPlanReplacesInline,
        TrafficSignPlanReplacedByInline,
    )
    initial_values = shared_initial_values

    def get_queryset(self, request):
        # NOTE: This get_queryset was generated by the admin_assist_get_queryset command.
        # If it is in need of updates, try generating a new one with the command again.

        qs = super().get_queryset(request)

        # Applying Custom Transformations
        qs = self.annotate_additional_signs(qs)

        # Optimizing Forward Relations (Joins)
        qs = qs.select_related(
            "device_type",
            "device_type__icon_file",
            "replacement_to_new",
        )

        # Limiting Columns (Projection)
        qs = qs.only(
            "device_type__code",
            "device_type__description",
            "device_type__icon_file__file",
            "id",
            "lifecycle",
            "location",
            "replacement_to_new",
            "value",
        )

        return qs

    @annotate_queryset("annotate_additional_signs", "_has_additional_signs")
    @admin.display(description=_("has additional signs"))
    def has_additional_signs(self, obj):
        # Don't call obj.has_additional_signs() directly, because it will cause an explosion in query count
        # and lag the list view.
        is_active = getattr(obj, "_has_additional_signs", False)
        return _("Yes") if is_active else _("No")

    @staticmethod
    def annotate_additional_signs(qs):
        additional_signs_query = AdditionalSignPlan.objects.filter(
            parent=OuterRef("pk"),
            is_active=True,
        )
        return qs.annotate(_has_additional_signs=Exists(additional_signs_query))


class TrafficSignRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    model = TrafficSignRealFile
    formset = CityInfraFileUploadFormset


class TrafficSignRealInline(admin.TabularInline):
    model = TrafficSignReal
    verbose_name = _("Traffic Sign Real")
    verbose_name_plural = _("Traffic Sign Reals")
    fields = ("id", "device_type", "device_type_preview", "mount_type")
    readonly_fields = ("id", "device_type", "device_type_preview", "mount_type")
    show_change_link = True
    can_delete = False
    extra = 0


class TrafficSignRealOperationInline(TrafficControlOperationInlineBase):
    model = TrafficSignRealOperation


@admin.register(TrafficSignReal)
class TrafficSignRealAdmin(
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
):
    plan_model_field_name = "traffic_sign_plan"
    resource_class = TrafficSignRealResource
    form = TrafficSignRealModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "device_type",
                    "device_type_preview",
                    "mount_type",
                    "permit_decision_id",
                    "attachment_url",
                    "scanned_at",
                    "operation",
                    "manufacturer",
                    "rfid",
                    "value",
                    "txt",
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
                    "reflection_class",
                    "surface_class",
                    "condition",
                    "double_sided",
                    "peak_fastened",
                )
            },
        ),
        (_("Related models"), {"fields": ("traffic_sign_plan", "mount_real")}),
        (
            _("Installation information"),
            {
                "fields": (
                    "installation_date",
                    "installation_status",
                    "installation_id",
                    "installation_details",
                ),
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
        "traffic_sign_plan",
        "device_type_preview",
        "legacy_code",
        "value",
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
        "seasonal_validity_period_information",
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
        "txt",
        "has_additional_signs",
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
        "device_type_preview",
        "has_additional_signs",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "source_name",
        "source_id",
    )
    raw_id_fields = ("traffic_sign_plan", "mount_real")
    ordering = ("-created_at",)
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ("lifecycle", EnumFieldListFilter),
        ("installation_status", EnumFieldListFilter),
        ("condition", EnumFieldListFilter),
        ("reflection_class", EnumFieldListFilter),
        ("surface_class", EnumFieldListFilter),
        ("location_specifier", EnumFieldListFilter),
        "owner",
        OperationalAreaListFilter,
    ]
    search_fields = (
        "value",
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
        TrafficSignRealFileInline,
        TrafficSignRealOperationInline,
        AdditionalSignRealInline,
    )
    initial_values = {
        **shared_initial_values,
        "condition": Condition.VERY_GOOD,
        "installation_status": InstallationStatus.IN_USE,
    }

    def get_queryset(self, request):
        # NOTE: This get_queryset was generated by the admin_assist_get_queryset command.
        # If it is in need of updates, try generating a new one with the command again.

        qs = super().get_queryset(request)

        # Applying Custom Transformations
        qs = self.annotate_additional_signs(qs)

        # Optimizing Forward Relations (Joins)
        qs = qs.select_related(
            "created_by",
            "device_type",
            "device_type__icon_file",
            "mount_real",
            "mount_real__mount_type",
            "mount_type",
            "owner",
            "traffic_sign_plan",
            "traffic_sign_plan__device_type",
            "updated_by",
        )

        # Limiting Columns (Projection)
        qs = qs.only(
            "attachment_url",
            "condition",
            "created_at",
            "created_by",
            "created_by__email",
            "created_by__first_name",
            "created_by__last_name",
            "device_type",
            "device_type__code",
            "device_type__description",
            "device_type__icon_file__file",
            "direction",
            "height",
            "id",
            "installation_date",
            "installation_details",
            "installation_id",
            "installation_status",
            "lane_number",
            "lane_type",
            "legacy_code",
            "lifecycle",
            "location_specifier",
            "manufacturer",
            "mount_real",
            "mount_real__mount_type",
            "mount_real__mount_type__code",
            "mount_real__mount_type__description",
            "mount_type",
            "mount_type__code",
            "mount_type__description",
            "operation",
            "owner",
            "owner__name_en",
            "owner__name_fi",
            "permit_decision_id",
            "reflection_class",
            "rfid",
            "road_name",
            "scanned_at",
            "seasonal_validity_period_information",
            "size",
            "source_id",
            "source_name",
            "surface_class",
            "traffic_sign_plan",
            "traffic_sign_plan__device_type",
            "txt",
            "updated_at",
            "updated_by",
            "updated_by__email",
            "updated_by__first_name",
            "updated_by__last_name",
            "validity_period_end",
            "validity_period_start",
            "value",
        )

        return qs

    @annotate_queryset("annotate_additional_signs", "_has_additional_signs")
    @admin.display(description=_("has additional signs"))
    def has_additional_signs(self, obj):
        # Don't call obj.has_additional_signs() directly, because it will cause an explosion in query count
        # and lag the list view.
        is_active = getattr(obj, "_has_additional_signs", False)
        return _("Yes") if is_active else _("No")

    @staticmethod
    def annotate_additional_signs(qs):
        additional_signs_query = AdditionalSignPlan.objects.filter(
            parent=OuterRef("pk"),
            is_active=True,
        )
        return qs.annotate(_has_additional_signs=Exists(additional_signs_query))
