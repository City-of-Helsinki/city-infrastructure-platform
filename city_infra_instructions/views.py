from django.contrib.admindocs.views import BaseAdminDocsView
from django.template.loader import render_to_string
from django.utils.translation import gettext as _


class InstructionsIndexView(BaseAdminDocsView):
    template_name = "city_infra_instructions/instructions_index.html"

    def has_app_permission(self, app_code: str) -> bool:
        """Return true if user has any permissions to models in the given app"""

        if self.request.user.is_superuser:
            return True

        user_permissions = self.request.user.get_all_permissions()
        user_app_permissions = {p.split(".")[0] for p in user_permissions}
        return app_code in user_app_permissions

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

        if self.has_app_permission("city_furniture"):
            sections.extend(
                [
                    {
                        "category": "City Furniture",
                        "name": _("Importer"),
                        "description": _("The importer can be used to import data into the platform"),
                        "body": render_to_string("city_infra_instructions/instructions/importer.html"),
                    },
                    {
                        "category": "City Furniture",
                        "name": _("Exporter"),
                        "description": _("The exporter can be used to export data from the platform"),
                        "body": render_to_string("city_infra_instructions/instructions/exporter.html"),
                    },
                ]
            )

        return super().get_context_data(**{**kwargs, "sections": sections})
