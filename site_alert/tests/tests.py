from importlib import import_module

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import translation

from site_alert.context_processors import site_alerts as alerts_context_processor

from .factories import SiteAlertFactory


@pytest.mark.django_db
def test_translated_message_returns_correct_language():
    """
    Test that the property returns the correct language field.
    """
    alert = SiteAlertFactory(message_en="Hello", message_fi="Hei", message_sv="Hej")

    with translation.override("en"):
        assert alert.translated_message == "Hello"

    with translation.override("fi"):
        assert alert.translated_message == "Hei"

    with translation.override("sv"):
        assert alert.translated_message == "Hej"


@pytest.mark.django_db
def test_translated_message_fallback():
    """
    Test fallback to English when specific language is empty.
    """
    alert = SiteAlertFactory(message_en="Fallback Content")

    with translation.override("fi"):
        assert alert.translated_message == "Fallback Content"


@pytest.mark.django_db
def test_dismiss_alert_updates_session(client):
    """
    Test that hitting the dismiss endpoint adds the ID to the session.
    """
    alert = SiteAlertFactory()

    url = reverse("site_alert:dismiss", args=[alert.id])
    response = client.post(url)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert alert.id in client.session["dismissed_alerts"]


@pytest.mark.django_db
def test_context_processor_logic(rf):
    """
    Test the context processor filters out dismissed alerts.
    """
    alert_active = SiteAlertFactory(message_en="I stay")
    alert_dismissed = SiteAlertFactory(message_en="I go")

    request = rf.get("/")
    engine = import_module(settings.SESSION_ENGINE)
    request.session = engine.SessionStore()

    request.session["dismissed_alerts"] = [alert_dismissed.id]
    request.session.save()

    context = alerts_context_processor(request)

    assert alert_active in context["site_alerts"]
    assert alert_dismissed not in context["site_alerts"]


@pytest.mark.django_db
def test_inactive_alerts_hidden(rf):
    """
    Ensure is_active=False alerts are never shown.
    """
    active_alert = SiteAlertFactory(is_active=True)
    inactive_alert = SiteAlertFactory(is_active=False)

    request = rf.get("/")
    engine = import_module(settings.SESSION_ENGINE)
    request.session = engine.SessionStore()

    context = alerts_context_processor(request)

    assert active_alert in context["site_alerts"]
    assert inactive_alert not in context["site_alerts"]
