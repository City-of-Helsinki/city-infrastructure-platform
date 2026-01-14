from django.urls import path

from . import views

app_name = "site_alert"

urlpatterns = [
    path("dismiss/<int:alert_id>/", views.dismiss_alert, name="dismiss"),
]
