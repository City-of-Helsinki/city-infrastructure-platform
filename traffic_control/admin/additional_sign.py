from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _

from ..constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from ..forms import AdditionalSignPlanModelForm, AdditionalSignRealModelForm
from ..mixins import (
    Point3DFieldAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
)
from ..models import (
    AdditionalSignContentPlan,
    AdditionalSignContentReal,
    AdditionalSignPlan,
    AdditionalSignReal,
)
from .audit_log import AuditLogHistoryAdmin


class BaseAdditionalSignContentInline(admin.TabularInline):
    model = None
    fields = (
        "order",
        "text",
        "device_type",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    verbose_name = _("Additional sign content")
    verbose_name_plural = _("Additional sign contents")
    extra = 0
    ordering = ("order",)


class AdditionalSignContentPlanInline(BaseAdditionalSignContentInline):
    model = AdditionalSignContentPlan


class AdditionalSignContentRealInline(BaseAdditionalSignContentInline):
    model = AdditionalSignContentReal


@admin.register(AdditionalSignPlan)
class AdditionalSignPlanAdmin(
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
    Point3DFieldAdminMixin,
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
    form = AdditionalSignPlanModelForm
    fields = (
        ("location", "z_coord"),
        "plan",
        "decision_date",
        "decision_id",
        "validity_period_start",
        "validity_period_end",
        "affect_area",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "reflection_class",
        "surface_class",
        "seasonal_validity_period_start",
        "seasonal_validity_period_end",
        "owner",
        "color",
        "lifecycle",
        "road_name",
        "lane_number",
        "lane_type",
        "location_specifier",
        "source_id",
        "source_name",
    )

    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    ordering = ("-created_at",)
    inlines = (AdditionalSignContentPlanInline,)


@admin.register(AdditionalSignReal)
class AdditionalSignRealAdmin(
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
    Point3DFieldAdminMixin,
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
    form = AdditionalSignRealModelForm
    fields = (
        "additional_sign_plan",
        ("location", "z_coord"),
        "validity_period_start",
        "validity_period_end",
        "affect_area",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "reflection_class",
        "surface_class",
        "seasonal_validity_period_start",
        "seasonal_validity_period_end",
        "owner",
        "color",
        "lifecycle",
        "road_name",
        "lane_number",
        "lane_type",
        "location_specifier",
        "condition",
        "manufacturer",
        "rfid",
        "source_id",
        "source_name",
    )
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    ordering = ("-created_at",)
    inlines = (AdditionalSignContentRealInline,)
