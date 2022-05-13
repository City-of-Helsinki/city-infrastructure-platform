from django.contrib.admindocs import views as admindoc_views
from django.urls import path, re_path

from city_infra_instructions import views

urlpatterns = [
    path(
        "",
        views.BaseAdminDocsView.as_view(template_name="city_infra_instructions/index.html"),
        name="django-admindocs-docroot",
    ),
    path(
        "instructions/",
        views.InstructionsIndexView.as_view(),
        name="django-admindocs-instructions",
    ),
    ),
]
