from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView


@method_decorator(staff_member_required, name="dispatch")
class MyAccountView(TemplateView):
    template_name = "admin/my_account.html"
    title = _("My account")

    def get_context_data(self, **kwargs):
        context = {
            **super().get_context_data(**kwargs),
            **admin.site.each_context(self.request),
        }
        context["title"] = self.title

        user = self.request.user
        context["user"] = user

        return context
