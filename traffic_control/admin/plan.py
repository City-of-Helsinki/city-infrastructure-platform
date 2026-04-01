import csv
import re
from copy import copy
from typing import Any, Dict, List

from admin_confirm import AdminConfirmMixin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.contrib.gis import admin
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import DateRangeFilterBuilder

from traffic_control.admin.admin_filters import as_dropdown
from traffic_control.admin.audit_log import AuditLogHistoryAdmin
from traffic_control.forms import PlanModelForm, PlanRelationsForm
from traffic_control.mixins import (
    EnumChoiceValueDisplayAdminMixin,
    Geometry3DFieldAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
)
from traffic_control.mixins.models import ValidityPeriodModel
from traffic_control.models import Plan, PlanGeometryImportLog

__all__ = ("PlanAdmin", "PlanGeometryImportLogAdmin")


@admin.register(Plan)
class PlanAdmin(
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    Geometry3DFieldAdminMixin,
    AdminConfirmMixin,
    admin.GISModelAdmin,
    AuditLogHistoryAdmin,
):
    form = PlanModelForm
    SHOW_Z_COORD = False
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "id",
                    "name",
                    "decision_id",
                    "decision_date",
                    "diary_number",
                    "drawing_numbers",
                    "decision_url",
                    "source_id",
                    "source_name",
                )
            },
        ),
        (_("Location information"), {"fields": ("derive_location", "location", "z_coord", "location_ewkt")}),
        (
            _("Metadata"),
            {"fields": ("created_at", "updated_at", "created_by", "updated_by")},
        ),
    )
    list_display = ("id", "decision_id", "name", "diary_number", "drawing_numbers", "created_at")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    ordering = ("-created_at",)
    search_fields = (
        "decision_id",
        "diary_number",
        "drawing_numbers",
        "id",
        "name",
        "source_name",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ("created_by", as_dropdown(RelatedOnlyFieldListFilter)),
        ("updated_by", as_dropdown(RelatedOnlyFieldListFilter)),
        ("created_at", DateRangeFilterBuilder()),
        ("updated_at", DateRangeFilterBuilder()),
        ("decision_date", DateRangeFilterBuilder()),
    ]

    confirm_change = True
    confirmation_fields = ["location"]
    change_confirmation_template = "admin/traffic_control/plan/change_confirmation.html"
    only_form_fields = ["location_ewkt"]

    def get_confirmation_fields(self, request, obj=None):
        """This is an overridden function from AdminConfirmMixin for getting confirmation fields dynamically."""
        base_fields = copy(super().get_confirmation_fields(request, obj))
        if request.POST.get("derive_location") != "on":
            # location should always be there
            base_fields.remove("location")
        return base_fields

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/set-plans/",
                self.admin_site.admin_view(self.set_plan_relations_view),
                name="traffic_control_plan_set-plans",
            )
        ]
        return custom_urls + urls

    def set_plan_relations_view(self, request, object_id):
        template_name = "admin/traffic_control/plan/plan_relations.html"
        user = request.user

        if not user.has_perm(Plan.VIEW_PERMISSION):
            return HttpResponseForbidden()

        plan = get_object_or_404(Plan, pk=object_id)

        context = {
            **self.admin_site.each_context(request),
            "title": _("Set related plans for plan %s") % plan,
            "plan": plan,
        }

        if request.method == "POST":
            if not user.has_perm(Plan.CHANGE_PERMISSION):
                return HttpResponseForbidden()

            form = PlanRelationsForm(request.POST, plan=plan)

            if form.is_valid():
                cleaned_data = form.cleaned_data

                # Set the relation to `None` for instances that were unselected
                for field, selected_qs in cleaned_data.items():
                    old_selections_qs = getattr(plan, field)
                    unselected_qs = old_selections_qs.exclude(pk__in=selected_qs)
                    unselected_qs.update(plan=None)

                # Set the relation to `plan` for all instances that were selected
                for field, selected_qs in cleaned_data.items():
                    if issubclass(selected_qs.model, ValidityPeriodModel):
                        # For ValidityPeriodModel subclasses, we need to ensure
                        # that the validity_period_start matches the plan's decision_date
                        selected_qs.update(plan=plan, validity_period_start=plan.decision_date)
                    else:
                        selected_qs.active().update(plan=plan)

            if "_save" in request.POST and not form.errors:
                # "Save" button was pressed. Redirect to admin plan list view.
                return HttpResponseRedirect(reverse("admin:traffic_control_plan_changelist"))

            context["form"] = form

        if request.method == "GET":
            initial = {
                "barrier_plans": plan.barrier_plans.active(),
                "mount_plans": plan.mount_plans.active(),
                "road_marking_plans": plan.road_marking_plans.active(),
                "signpost_plans": plan.signpost_plans.active(),
                "traffic_light_plans": plan.traffic_light_plans.active(),
                "traffic_sign_plans": plan.traffic_sign_plans.active(),
                "additional_sign_plans": plan.additional_sign_plans.all(),
                "furniture_signpost_plans": plan.furniture_signpost_plans.active(),
            }
            context["form"] = PlanRelationsForm(plan=plan, initial=initial)

        return render(request, template_name, context)


@admin.register(PlanGeometryImportLog)
class PlanGeometryImportLogAdmin(admin.ModelAdmin):
    class Media:
        js = ("traffic_control/js/toggle_import_geometry_results_table.js",)
        css = {"all": ("traffic_control/css/import_geometry_results_table.css",)}

    list_display = (
        "start_time",
        "file_path",
        "dry_run",
        "total_rows",
        "success_count",
        "error_count",
        "end_time",
    )
    list_filter = (
        "dry_run",
        ("start_time", DateRangeFilterBuilder()),
    )
    readonly_fields = (
        "id",
        "start_time",
        "end_time",
        "file_path",
        "output_dir",
        "dry_run",
        "total_rows",
        "success_count",
        "error_count",
        "skipped_count",
        "success_details",
        "skipped_no_changes_details",
        "missing_diary_number_details",
        "duplicate_diary_number_details",
        "plan_not_found_details",
        "decision_id_mismatch_details",
        "drawing_number_mismatch_details",
        "invalid_wkt_details",
        "invalid_geometry_type_details",
        "invalid_geometry_topology_details",
        "invalid_geometry_bounds_details",
        "empty_geometry_details",
        "results",
    )

    fieldsets = (
        (
            _("Import Information"),
            {
                "fields": (
                    "id",
                    "start_time",
                    "end_time",
                    "file_path",
                    "output_dir",
                    "dry_run",
                )
            },
        ),
        (
            _("Results Summary"),
            {
                "fields": (
                    "total_rows",
                    "success_count",
                    "skipped_count",
                    "error_count",
                )
            },
        ),
        (
            _("Successful Imports"),
            {
                "fields": ("success_details", "skipped_no_changes_details"),
            },
        ),
        (
            _("Data Validation Errors"),
            {
                "fields": (
                    "missing_diary_number_details",
                    "duplicate_diary_number_details",
                    "plan_not_found_details",
                    "decision_id_mismatch_details",
                    "drawing_number_mismatch_details",
                ),
            },
        ),
        (
            _("Geometry Errors"),
            {
                "fields": (
                    "invalid_wkt_details",
                    "invalid_geometry_type_details",
                    "invalid_geometry_topology_details",
                    "invalid_geometry_bounds_details",
                    "empty_geometry_details",
                ),
            },
        ),
        (
            _("Raw JSON Results"),
            {
                "fields": ("results",),
                "classes": ("collapse",),
            },
        ),
    )

    def get_urls(self):
        """Inject custom routing into the admin namespace for this model."""
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name

        custom_urls = [
            path(
                "<path:object_id>/download-csv/<str:result_type>/",
                self.admin_site.admin_view(self.download_csv_view),
                name=f"{info[0]}_{info[1]}_download_csv",
            ),
        ]
        return custom_urls + urls

    def _prepare_row_data(self, result: dict, result_type: str) -> dict:
        """
        Normalizes a raw result dict into a standardized dictionary
        consumable by both the CSV exporter and the HTML template.
        """
        is_success = result_type in ("success", "skipped_no_changes")

        row_data = {
            "row_number": result.get("row_number", ""),
            "diary_number": result.get("diaari", ""),
            "fid": result.get("fid", ""),
            "drawing_number": result.get("piirustusnumero", ""),
            "decision_id": result.get("decision_id", ""),
            "is_success_type": is_success,
        }

        if is_success:
            row_data["plan_id"] = result.get("plan_id", "")
            # Extract changes into a structured list of dicts
            changes = []
            update_details = result.get("update_details", {})
            if update_details:
                changes = update_details.get("fields_changed", [])
            row_data["changes"] = changes
            row_data["has_changes"] = bool(changes)
        else:
            row_data["error_message"] = result.get("error_message", "")

        return row_data

    def download_csv_view(self, request: HttpRequest, object_id: str, result_type: str) -> HttpResponse:
        """Main entry point for downloading import results as CSV."""
        obj = get_object_or_404(PlanGeometryImportLog, pk=object_id)

        is_summary = request.GET.get("mode", "summary") == "summary"
        is_success_type = result_type in ("success", "skipped_no_changes")

        # 1. Gather and normalize data
        filtered_results = [r for r in obj.results if r.get("result_type") == result_type] if obj.results else []
        prepared_rows = [self._prepare_row_data(r, result_type) for r in filtered_results]

        # 2. Setup HTTP Response
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response.write("\ufeff".encode("utf8"))  # BOM for Excel

        filename_suffix = "" if is_summary or not is_success_type else "_detailed"
        filename = f"plan_import_{result_type}{filename_suffix}_{object_id}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response, delimiter=";", quoting=csv.QUOTE_NONNUMERIC)

        # 3. Route to the correct writer
        if is_success_type:
            self._write_success_csv(writer, prepared_rows, is_summary)
        else:
            self._write_error_csv(writer, prepared_rows)

        return response

    def _write_error_csv(self, writer: Any, rows: List[Dict[str, Any]]) -> None:
        """Writes the flat, simple error CSV."""
        writer.writerow(["Row", "Diary Number", "FID", "Drawing #", "Decision ID", "Error"])

        for data in rows:
            writer.writerow(
                [
                    data["row_number"],
                    data["diary_number"],
                    data["fid"],
                    data["drawing_number"],
                    data["decision_id"],
                    data.get("error_message", ""),
                ]
            )

    @staticmethod
    def _count_polygons(val: str) -> str:
        if val == "None":
            return "None"
        count = len(re.findall(r"\(\(\(", val))
        return f"MultiPolygon ({count} polygons)"

    def _write_success_csv(self, writer: Any, rows: List[Dict[str, Any]], is_summary: bool) -> None:
        """Writes the success/skipped CSV, handling the complex change formatting."""
        writer.writerow(["Row", "Diary Number", "FID", "Drawing #", "Decision ID", "Plan ID", "Fields Changed"])

        for data in rows:
            base_columns = [
                data["row_number"],
                data["diary_number"],
                data["fid"],
                data["drawing_number"],
                data["decision_id"],
                data.get("plan_id", ""),
            ]

            # Early return for no changes
            if not data.get("has_changes"):
                fields_changed = "No changes" if "changes" in data else "N/A (dry-run)"
                writer.writerow(base_columns + [fields_changed])
                continue

            # Format changes
            formatted_changes = []
            for fc in data["changes"]:
                field = fc.get("field")
                old_val = str(fc.get("old_value", ""))
                new_val = str(fc.get("new_value", ""))

                if is_summary and field == "location":
                    formatted_changes.append(
                        f"{field}: {self._count_polygons(old_val)} → {self._count_polygons(new_val)}"
                    )
                else:
                    formatted_changes.append(f"{field}: {old_val} → {new_val}")

            separator = "; " if is_summary else " | "
            writer.writerow(base_columns + [separator.join(formatted_changes)])

    def _format_results(self, obj: PlanGeometryImportLog, result_type: str) -> str:
        """Format results of a specific type by passing shared data to a Django template."""
        if not obj.results:
            return "-"

        filtered_results = [r for r in obj.results if r.get("result_type") == result_type]
        if not filtered_results:
            return "-"

        # Prepare rows using the shared utility (limit to 100 for HTML performance)
        prepared_rows = [self._prepare_row_data(r, result_type) for r in filtered_results[:100]]

        # Generate the base URL for the download view
        info = self.model._meta.app_label, self.model._meta.model_name
        download_url = reverse(f"admin:{info[0]}_{info[1]}_download_csv", args=[obj.id, result_type])

        context = {
            "result_type": result_type,
            "total_count": len(filtered_results),
            "rows": prepared_rows,
            "is_success_type": result_type in ("success", "skipped_no_changes"),
            "download_url": download_url,
        }

        return render_to_string("admin/traffic_control/plan/import_geometry_results_table.html", context)

    @admin.display(description=_("Successfully Imported Plans"))
    def success_details(self, obj: PlanGeometryImportLog) -> str:
        """Get formatted HTML table of successfully imported plans.

        Args:
            obj (PlanGeometryImportLog): The import log instance.

        Returns:
            str: HTML formatted table with successful import details.
        """
        return self._format_results(obj, "success")

    @admin.display(description=_("Skipped (No Changes Needed)"))
    def skipped_no_changes_details(self, obj: PlanGeometryImportLog) -> str:
        """Get formatted HTML table of plans skipped because geometry matched.

        Args:
            obj (PlanGeometryImportLog): The import log instance.

        Returns:
            str: HTML formatted table with skipped plan details.
        """
        return self._format_results(obj, "skipped_no_changes")

    @admin.display(description=_("Missing Diary Numbers"))
    def missing_diary_number_details(self, obj: PlanGeometryImportLog) -> str:
        """Get formatted HTML table of rows with missing diary numbers.

        Args:
            obj (PlanGeometryImportLog): The import log instance.

        Returns:
            str: HTML formatted table with missing diary number errors.
        """
        return self._format_results(obj, "missing_diary_number")

    @admin.display(description=_("Duplicate Diary Numbers"))
    def duplicate_diary_number_details(self, obj: PlanGeometryImportLog) -> str:
        """Get formatted HTML table of rows with duplicate diary numbers in CSV.

        Args:
            obj (PlanGeometryImportLog): The import log instance.

        Returns:
            str: HTML formatted table with duplicate diary number errors.
        """
        return self._format_results(obj, "duplicate_diary_number")

    @admin.display(description=_("Invalid WKT Geometry"))
    def invalid_wkt_details(self, obj: PlanGeometryImportLog) -> str:
        """Get formatted HTML table of rows with invalid WKT geometry.

        Args:
            obj (PlanGeometryImportLog): The import log instance.

        Returns:
            str: HTML formatted table with invalid WKT errors.
        """
        return self._format_results(obj, "invalid_wkt")

    @admin.display(description=_("Invalid Geometry Type"))
    def invalid_geometry_type_details(self, obj: PlanGeometryImportLog) -> str:
        """Get formatted HTML table of rows with wrong geometry type.

        Args:
            obj (PlanGeometryImportLog): The import log instance.

        Returns:
            str: HTML formatted table with geometry type errors.
        """
        return self._format_results(obj, "invalid_geometry_type")

    @admin.display(description=_("Invalid Geometry Topology"))
    def invalid_geometry_topology_details(self, obj: PlanGeometryImportLog) -> str:
        """Get formatted HTML table of rows with topologically invalid geometries.

        Args:
            obj (PlanGeometryImportLog): The import log instance.

        Returns:
            str: HTML formatted table with topology validation errors.
        """
        return self._format_results(obj, "invalid_geometry_topology")

    @admin.display(description=_("Out of Bounds Geometries"))
    def invalid_geometry_bounds_details(self, obj: PlanGeometryImportLog) -> str:
        """Get formatted HTML table of rows with geometries outside valid projection bounds.

        Args:
            obj (PlanGeometryImportLog): The import log instance.

        Returns:
            str: HTML formatted table with out of bounds errors.
        """
        return self._format_results(obj, "invalid_geometry_bounds")

    @admin.display(description=_("Empty Geometries"))
    def empty_geometry_details(self, obj: PlanGeometryImportLog) -> str:
        """Get formatted HTML table of rows with empty geometries.

        Args:
            obj (PlanGeometryImportLog): The import log instance.

        Returns:
            str: HTML formatted table with empty geometry errors.
        """
        return self._format_results(obj, "empty_geometry")

    @admin.display(description=_("Plans Not Found"))
    def plan_not_found_details(self, obj: PlanGeometryImportLog) -> str:
        """Get formatted HTML table of rows where no matching Plan was found.

        Args:
            obj (PlanGeometryImportLog): The import log instance.

        Returns:
            str: HTML formatted table with plan not found errors.
        """
        return self._format_results(obj, "plan_not_found")

    @admin.display(description=_("Decision ID Mismatches"))
    def decision_id_mismatch_details(self, obj: PlanGeometryImportLog) -> str:
        """Get formatted HTML table of rows with decision_id mismatch.

        Args:
            obj (PlanGeometryImportLog): The import log instance.

        Returns:
            str: HTML formatted table with decision ID mismatch errors.
        """
        return self._format_results(obj, "decision_id_mismatch")

    @admin.display(description=_("Drawing Number Mismatches"))
    def drawing_number_mismatch_details(self, obj: PlanGeometryImportLog) -> str:
        """Get formatted HTML table of rows with drawing number mismatch.

        Args:
            obj (PlanGeometryImportLog): The import log instance.

        Returns:
            str: HTML formatted table with drawing number mismatch errors.
        """
        return self._format_results(obj, "drawing_number_mismatch")

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
