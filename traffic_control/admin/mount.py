from django.contrib.gis import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter

from traffic_control.admin.audit_log import AuditLogHistoryAdmin
from traffic_control.admin.common import TrafficControlOperationInlineBase
from traffic_control.admin.traffic_sign import OrderedTrafficSignRealInline
from traffic_control.admin.utils import (
    DeviceComparisonAdminMixin,
    ResponsibleEntityPermissionAdminMixin,
    ResponsibleEntityPermissionFilter,
    TreeModelFieldListFilter,
)
from traffic_control.constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from traffic_control.forms import AdminFileWidget
from traffic_control.mixins import (
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
)
from traffic_control.models import MountPlan, MountPlanFile, MountReal, MountRealFile, MountType, PortalType

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


@admin.register(MountPlan)
class MountPlanAdmin(
    ResponsibleEntityPermissionAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "responsible_entity",
                    "electric_accountable",
                    "txt",
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
    raw_id_fields = ("plan",)
    ordering = ("-created_at",)
    inlines = (MountPlanFileInline,)


class MountRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = MountRealFile


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
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
    plan_model_field_name = "mount_plan"
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
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
