from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _

from ..constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from ..mixins import (
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
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
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
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
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
