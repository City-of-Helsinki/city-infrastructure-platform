from copy import copy
from typing import Dict

from admin_confirm import AdminConfirmMixin
from django.contrib.gis import admin
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

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
    )

    confirm_change = True
    confirmation_fields = ["location"]
    change_confirmation_template = "admin/traffic_control/plan/change_confirmation.html"
    only_form_fields = ["location_ewkt"]

    def get_confirmation_fields(self, request, obj=None):
        """This is an overridden function from CityInfraAdminConfirmMixin(AdminConfirmMixin)
        for getting confirmation fields dynamically.
        """
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
    list_display = (
        "start_time",
        "file_path",
        "dry_run",
        "total_rows",
        "success_count",
        "error_count",
        "end_time",
    )
    list_filter = ("dry_run", "start_time")
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

    def _generate_csv_download_script(
        self,
        result_type: str,
        csv_data_json: str,
        summary_mode: bool,
        obj_id: str,
        use_mode_suffix: bool = True,
    ) -> str:
        """Generate JavaScript for CSV download functionality.

        Args:
            result_type (str): Type of results (success, skipped_no_changes, etc.).
            csv_data_json (str): JSON string of CSV data.
            summary_mode (bool): If True, generate summary CSV; if False, generate detailed CSV.
            obj_id (str): ID of the log object for filename.
            use_mode_suffix (bool): If True, add _summary/_detailed suffix to function name. Defaults to True.

        Returns:
            str: JavaScript code for CSV download.
        """
        if use_mode_suffix:
            mode_suffix = "_summary" if summary_mode else "_detailed"
        else:
            mode_suffix = ""
        filename_suffix = "" if summary_mode else "_detailed"

        script = f"""
        <script>
        var csvData_{result_type}{mode_suffix} = {csv_data_json};
        function downloadCSV_{result_type}{mode_suffix}() {{
          var headers = ["Row", "Diary Number", "FID", "Drawing #", "Decision ID"];
          if ("{result_type}" === "success" || "{result_type}" === "skipped_no_changes") {{
            headers.push("Plan ID");
            headers.push("Fields Changed");
          }} else {{
            headers.push("Error");
          }}
          var csv = headers.join(";") + "\\n";
          csvData_{result_type}{mode_suffix}.forEach(function(row) {{
            var line = [
              row.row_number,
              "\\"" + (row.diaari || "").replace(/"/g, '\\"') + "\\"",
              row.fid,
              row.piirustusnumero,
              row.decision_id,
            ];
            if ("{result_type}" === "success" || "{result_type}" === "skipped_no_changes") {{
              line.push(row.plan_id);
              """

        if summary_mode:
            # Summary mode: Create human-readable fields_changed from update_details
            script += """
              // Generate summary from update_details
              var fieldsChanged = "N/A";
              if (row.update_details && row.update_details.fields_changed) {{
                var changes = [];
                row.update_details.fields_changed.forEach(function(fc) {{
                  if (fc.field === "location") {{
                    // Show polygon count instead of full EWKT
                    var oldVal = fc.old_value;
                    var newVal = fc.new_value;
                    var oldSummary = oldVal === "None" ? "None" : (
                      "MultiPolygon (" + (oldVal.match(/\\(\\(\\(/g) || []).length + " polygons)"
                    );
                    var newSummary = (
                      "MultiPolygon (" + (newVal.match(/\\(\\(\\(/g) || []).length + " polygons)"
                    );
                    changes.push(fc.field + ": " + oldSummary + " → " + newSummary);
                  }} else {{
                    changes.push(fc.field + ": " + fc.old_value + " → " + fc.new_value);
                  }}
                }});
                fieldsChanged = changes.length > 0 ? changes.join("; ") : "No changes";
              }}
              line.push("\\"" + fieldsChanged.replace(/"/g, '\\"') + "\\"");
            """
        else:
            # Detailed mode: Show full EWKT values
            script += """
              // Generate detailed from update_details with full EWKT
              var fieldsChanged = "N/A";
              if (row.update_details && row.update_details.fields_changed) {{
                var changes = [];
                row.update_details.fields_changed.forEach(function(fc) {{
                  changes.push(fc.field + ": " + fc.old_value + " → " + fc.new_value);
                }});
                fieldsChanged = changes.length > 0 ? changes.join(" | ") : "No changes";
              }}
              line.push("\\"" + fieldsChanged.replace(/"/g, '\\"') + "\\"");
            """

        script += f"""
            }} else {{
              line.push("\\"" + (row.error_message || "").replace(/"/g, '\\"') + "\\"");
            }}
            csv += line.join(";") + "\\n";
          }});
          var blob = new Blob([csv], {{ type: "text/csv;charset=utf-8;" }});
          var link = document.createElement("a");
          var url = URL.createObjectURL(blob);
          link.setAttribute("href", url);
          link.setAttribute("download", "plan_import_{result_type}{filename_suffix}_{obj_id}.csv");
          link.style.visibility = "hidden";
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }}
        </script>
        """

        return script

    def _generate_download_buttons_html(self, result_type: str, show_both: bool) -> str:
        """Generate download button HTML.

        Args:
            result_type (str): Type of results.
            show_both (bool): If True, show both summary and detailed buttons.

        Returns:
            str: HTML string for download buttons.
        """
        if show_both:
            return (
                f'<div style="display: flex; gap: 5px;">'
                f'<button type="button" onclick="event.stopPropagation(); '
                f'downloadCSV_{result_type}_summary();" '
                f'style="padding: 5px 12px; background-color: #417690; color: white; border: none; '
                f'border-radius: 4px; cursor: pointer; font-size: 12px;" '
                f'title="Human-readable format">📊 Summary CSV</button>'
                f'<button type="button" onclick="event.stopPropagation(); '
                f'downloadCSV_{result_type}_detailed();" '
                f'style="padding: 5px 12px; background-color: #5a6c7d; color: white; border: none; '
                f'border-radius: 4px; cursor: pointer; font-size: 12px;" '
                f'title="Full EWKT values">🔬 Detailed CSV</button>'
                f"</div>"
            )
        else:
            return (
                f'<button type="button" onclick="event.stopPropagation(); '
                f'downloadCSV_{result_type}();" '
                f'style="padding: 5px 15px; background-color: #417690; color: white; border: none; '
                f'border-radius: 4px; cursor: pointer; font-size: 12px;">Download as CSV</button>'
            )

    def _generate_table_header(self, result_type: str) -> str:
        """Generate HTML table header based on result type.

        Args:
            result_type (str): Type of results (success, error types, etc.).

        Returns:
            str: HTML string for table header.
        """
        header_parts = [
            '<thead><tr style="background-color: #f0f0f0;">'
            + '<th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Row</th>'
            + '<th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Diary Number</th>'
            + '<th style="padding: 8px; border: 1px solid #ddd; text-align: left;">FID</th>'
            + '<th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Drawing #</th>'
            + '<th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Decision ID</th>'
        ]

        if result_type == "success":
            header_parts.append('<th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Plan ID</th>')
            header_parts.append(
                '<th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Fields Changed</th>'
            )
        else:
            header_parts.append('<th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Error</th>')

        header_parts.append("</tr></thead><tbody>")
        return "".join(header_parts)

    def _generate_table_row(self, result: Dict, result_type: str) -> str:
        """Generate HTML table row for a single result.

        Args:
            result (Dict): Result dictionary with row data.
            result_type (str): Type of results (success, error types, etc.).

        Returns:
            str: HTML string for table row.
        """
        cell_style = 'style="padding: 8px; border: 1px solid #ddd;"'
        row_parts = [
            '<tr style="border: 1px solid #ddd;">',
            f'<td {cell_style}>{result.get("row_number", "")}</td>',
            f'<td {cell_style}>{result.get("diaari", "")}</td>',
            f'<td {cell_style}>{result.get("fid", "")}</td>',
            f'<td {cell_style}>{result.get("piirustusnumero", "")}</td>',
            f'<td {cell_style}>{result.get("decision_id", "")}</td>',
        ]

        if result_type == "success":
            plan_id = result.get("plan_id", "")
            row_parts.append(f"<td {cell_style}><code>{plan_id}</code></td>")

            # Add fields changed information
            if "update_details" in result:
                fields_changed = result["update_details"].get("fields_changed", [])
                if fields_changed:
                    changes_html = "".join(
                        [
                            f"<div style='margin-bottom: 5px;'>"
                            f"<strong>{fc['field']}:</strong> "
                            f"<span style='color: #c00;'>{fc['old_value']}</span> → "
                            f"<span style='color: #0a0;'>{fc['new_value']}</span>"
                            f"</div>"
                            for fc in fields_changed
                        ]
                    )
                    row_parts.append(f"<td {cell_style}>{changes_html}</td>")
                else:
                    row_parts.append(f"<td {cell_style}><em>No changes (geometry matched)</em></td>")
            else:
                row_parts.append(f"<td {cell_style}><em>N/A (dry-run)</em></td>")
        else:
            error_msg = result.get("error_message", "")
            row_parts.append(f"<td {cell_style}><em>{error_msg}</em></td>")

        row_parts.append("</tr>")
        return "".join(row_parts)

    def _format_results(self, obj: PlanGeometryImportLog, result_type: str) -> str:
        """Format results of a specific type as HTML table.

        Args:
            obj (PlanGeometryImportLog): PlanGeometryImportLog instance to format results for.
            result_type (str): Type of results to display.

        Returns:
            str: HTML formatted string with table of results.
        """
        import json

        from django.utils.safestring import mark_safe

        if not obj.results:
            return "-"

        filtered_results = [r for r in obj.results if r.get("result_type") == result_type]

        if not filtered_results:
            return "-"

        # Prepare CSV data as JSON for JavaScript
        csv_data = []
        for result in filtered_results:
            is_success_type = result_type in ("success", "skipped_no_changes")
            csv_row = {
                "row_number": result.get("row_number", ""),
                "diaari": result.get("diaari", ""),
                "fid": result.get("fid", ""),
                "piirustusnumero": result.get("piirustusnumero", ""),
                "decision_id": result.get("decision_id", ""),
                "plan_id": result.get("plan_id", "") if is_success_type else "",
                "error_message": result.get("error_message", "") if not is_success_type else "",
            }
            # Add full update details for JavaScript processing (for both summary and detailed modes)
            if result_type in ("success", "skipped_no_changes") and "update_details" in result:
                csv_row["update_details"] = result["update_details"]
            csv_data.append(csv_row)

        csv_data_json = json.dumps(csv_data)

        # Determine if we need both summary and detailed download buttons
        show_both_downloads = result_type in ("success", "skipped_no_changes")

        # Create collapsible section with Django admin styling
        html_parts = [
            f'<fieldset class="module collapse-section" style="margin: 10px 0;">'
            f'<h2 style="cursor: pointer; user-select: none; background: #f8f8f8; padding: 10px; '
            f"margin: 0; border: 1px solid #ddd; display: flex; justify-content: space-between; "
            f'align-items: center;" onclick="toggleSection_{result_type}()">'
            f'<span style="display: flex; align-items: center; gap: 10px;">'
            f'<span class="toggle-icon" id="toggle_{result_type}" '
            f'style="display: inline-block; width: 20px;">▶</span> '
            f'<strong style="font-size: 16px; color: #333;">Count: {len(filtered_results)}</strong>'
            f"</span>"
        ]

        html_parts.append(self._generate_download_buttons_html(result_type, show_both_downloads))
        html_parts.append("</h2>")
        html_parts.append(
            '<div id="content_' + result_type + '" style="display: none; padding: 10px; '
            'border: 1px solid #ddd; border-top: none;">'
            "<script>"
            "function toggleSection_" + result_type + "() {"
            '  var content = document.getElementById("content_' + result_type + '");'
            '  var icon = document.getElementById("toggle_' + result_type + '");'
            '  if (content.style.display === "none") {'
            '    content.style.display = "block";'
            '    icon.textContent = "▼";'
            "  } else {"
            '    content.style.display = "none";'
            '    icon.textContent = "▶";'
            "  }"
            "}"
            "</script>"
        )

        # Generate CSV download script(s)
        if show_both_downloads:
            # Generate both summary and detailed download functions (with suffixes)
            html_parts.append(
                self._generate_csv_download_script(result_type, csv_data_json, True, str(obj.id), use_mode_suffix=True)
            )
            html_parts.append(
                self._generate_csv_download_script(result_type, csv_data_json, False, str(obj.id), use_mode_suffix=True)
            )
        else:
            # Generate single download function for errors (no suffix)
            html_parts.append(
                self._generate_csv_download_script(result_type, csv_data_json, True, str(obj.id), use_mode_suffix=False)
            )

        html_parts.append('<table style="width: 100%; border-collapse: collapse; font-size: 12px;">')
        html_parts.append(self._generate_table_header(result_type))

        for result in filtered_results[:100]:  # Limit to 100 rows for performance
            html_parts.append(self._generate_table_row(result, result_type))

        html_parts.append("</tbody></table>")

        if len(filtered_results) > 100:
            html_parts.append(
                f'<div style="margin: 10px 0; color: #666;">'
                f"<em>Showing first 100 of {len(filtered_results)} results in table. Download CSV for all results.</em>"
                f"</div>"
            )

        html_parts.append("</div></fieldset>")  # Close content div and fieldset

        return mark_safe("".join(html_parts))

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
