from django.contrib.gis import admin
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from ..constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from ..forms import PlanRelationsForm
from ..mixins import SoftDeleteAdminMixin, UserStampedAdminMixin
from ..models import Plan
from .audit_log import AuditLogHistoryAdmin

__all__ = ("PlanAdmin",)


@admin.register(Plan)
class PlanAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
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
                    selected_qs.active().update(plan=plan)

            if "_save" in request.POST and not form.errors:
                # "Save" button was pressed. Redirect to admin plan list view.
                return HttpResponseRedirect(
                    reverse("admin:traffic_control_plan_changelist")
                )

            context["form"] = form

        if request.method == "GET":
            initial = {
                "barrier_plans": plan.barrier_plans.active(),
                "mount_plans": plan.mount_plans.active(),
                "road_marking_plans": plan.road_marking_plans.active(),
                "signpost_plans": plan.signpost_plans.active(),
                "traffic_light_plans": plan.traffic_light_plans.active(),
                "traffic_sign_plans": plan.traffic_sign_plans.active(),
            }
            context["form"] = PlanRelationsForm(plan=plan, initial=initial)

        return render(request, template_name, context)
