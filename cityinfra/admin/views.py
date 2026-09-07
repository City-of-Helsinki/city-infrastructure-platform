from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView


class AdminTemplateView(TemplateView):
    title: str

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            **admin.site.each_context(self.request),
            "title": self.title,
            "user": self.request.user,
        }


@method_decorator(staff_member_required, name="dispatch")
class MyAccountView(AdminTemplateView):
    template_name = "admin/my_account.html"
    title = _("My account")


@method_decorator(staff_member_required, name="dispatch")
class FeatureDisabledView(AdminTemplateView):
    template_name = "admin/disabled_feature.html"
    title = _("Disabled feature")
