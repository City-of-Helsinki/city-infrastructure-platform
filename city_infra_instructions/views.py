from django.contrib.admindocs.views import BaseAdminDocsView
from django.template.loader import render_to_string
from django.utils.translation import gettext as _


class InstructionsIndexView(BaseAdminDocsView):
    template_name = "city_infra_instructions/instructions_index.html"

    def get_context_data(self, **kwargs):
        # Sections visible for every user
        sections = [
            {
                "category": "City Infra",
                "name": _("General"),
                "description": _("Short description"),
                "body": render_to_string("city_infra_instructions/instructions/general.html"),
            },
        ]
        return super().get_context_data(**{**kwargs, "sections": sections})
