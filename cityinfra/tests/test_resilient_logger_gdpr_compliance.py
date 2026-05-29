from typing import Any

import pytest
from auditlog.context import set_actor
from auditlog.models import LogEntry
from django.contrib.auth.models import Group, Permission
from django.test import override_settings
from helusers.models import ADGroup
from resilient_logger.resilient_logger import ResilientLogger
from resilient_logger.sources import AbstractLogSource, DjangoAuditLogSource
from resilient_logger.sources.abstract_log_source_entry import AbstractLogSourceEntry
from resilient_logger.sources.django_audit_log_source_entry import DjangoAuditLogSourceEntry
from resilient_logger.utils import get_resilient_logger_config

from traffic_control.models import AdditionalSignPlan
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    OperationalAreaFactory,
    ResponsibleEntityFactory,
    UserFactory,
)
from users.models import User

# Adapted from django-resilient-logger's own tests:
VALID_CONFIG_ALL_FIELDS = {
    "origin": "test",
    "environment": "dev",
    "sources": [
        {"class": "resilient_logger.sources.ResilientLogSource"},
        {"class": "resilient_logger.sources.DjangoAuditLogSource"},
    ],
    "targets": [
        {
            "class": "resilient_logger.targets.ProxyLogTarget",
            "name": "proxy-target",
        }
    ],
    "batch_limit": 5000,
    "chunk_size": 500,
    "submit_unsent_entries": True,
    "clear_sent_entries": True,
}


@pytest.fixture
@override_settings(RESILIENT_LOGGER=VALID_CONFIG_ALL_FIELDS)
def resilient_logger():
    return ResilientLogger.create()


@pytest.fixture
def actor():
    return UserFactory(
        email="erica.esimerkinen@example.com",
        first_name="Erika",
        last_name="Esimerkinen",
        username="erica_esimerkinen",
    )


@pytest.fixture
def user(actor):
    with set_actor(actor):
        return UserFactory(
            email="erkki.esimerkki@example.com",
            first_name="Erkki",
            last_name="Esimerkki",
            username="erkki_esimerkki",
        )


@pytest.fixture
def additional_sign_plan(actor):
    with set_actor(actor):
        return AdditionalSignPlanFactory(
            seasonal_validity_period_information="",
        )


@pytest.fixture(autouse=True)
def clear_config_cache():
    get_resilient_logger_config.cache_clear()
    yield


# Utility checks


def user_pii_leaks(user: User | UserFactory, logentry: AbstractLogSourceEntry):
    """
    Checks for user PII leaks in a LogEntry object
    """
    leaks = []
    document = logentry.get_document()
    audit_event = document["audit_event"]
    for user_field in ["email", "first_name", "last_name"]:
        for event_field in audit_event:
            # NOTE (2026-05-18 thiago)
            # This check is unreliable in cases such as very short strings or None values, our test strings are long
            # enough, plus "leaking" of None values is irrelevant for the tests.
            if str(getattr(user, user_field)) in str(audit_event[event_field]):
                leaks.append(f"User {user_field} found in LogEntry '{event_field}' field")
    return leaks


def value_referenced(value: Any, logentry: AbstractLogSource):
    """
    Checks for references to a particular value in a LogEntry object
    """
    return str(value) in str(logentry.get_document())


# Operations on User objects


@pytest.mark.django_db
def test__user_created_resilient_logger_does_not_leak_user_pii(user):
    auditlog_entry = LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.CREATE).last()
    resilient_log_entry = DjangoAuditLogSourceEntry(auditlog_entry)
    assert user_pii_leaks(user, resilient_log_entry) == [], "resilient log entry does not store user PII"
    assert value_referenced(user.pk, resilient_log_entry), "resilient log entry references user PK"


@pytest.mark.django_db
def test__user_updated_resilient_logger_does_not_leak_user_pii(user):
    user.email = "xavier.example@example.com"
    user.first_name = "Xavier"
    user.last_name = "Example"
    user.username = "xavier_example"
    user.save()
    auditlog_entry = LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.UPDATE).last()
    resilient_log_entry = DjangoAuditLogSourceEntry(auditlog_entry)
    assert user_pii_leaks(user, resilient_log_entry) == [], "resilient log entry does not store user PII"
    assert value_referenced(user.pk, resilient_log_entry), "resilient log entry references user PK"


@pytest.mark.django_db
def test__user_deleted_resilient_logger_does_not_leak_user_pii(user):
    user.delete()
    auditlog_entry = LogEntry.objects.get_for_model(User).filter(action=LogEntry.Action.DELETE).last()
    resilient_log_entry = DjangoAuditLogSourceEntry(auditlog_entry)
    assert user_pii_leaks(user, resilient_log_entry) == [], "resilient log entry does not store user PII"
    assert value_referenced(user.pk, resilient_log_entry), "resilient log entry references user PK"


# Operations on other objects


@pytest.mark.django_db
def test__object_created_resilient_logger_does_not_leak_actor_pii(actor, additional_sign_plan):
    auditlog_entry = LogEntry.objects.get_for_object(additional_sign_plan).filter(action=LogEntry.Action.CREATE).last()
    resilient_log_entry = DjangoAuditLogSourceEntry(auditlog_entry)
    assert user_pii_leaks(actor, resilient_log_entry) == [], "resilient log entry does not store actor PII"
    assert value_referenced(actor.pk, resilient_log_entry), "resilient log entry references actor PK"


@pytest.mark.django_db
def test__object_updated_resilient_logger_does_not_leak_actor_pii(actor, user, additional_sign_plan):
    with set_actor(actor):
        additional_sign_plan.updated_by = user
        additional_sign_plan.save()
    auditlog_entry = LogEntry.objects.get_for_object(additional_sign_plan).filter(action=LogEntry.Action.UPDATE).last()
    resilient_log_entry = DjangoAuditLogSourceEntry(auditlog_entry)
    assert user_pii_leaks(actor, resilient_log_entry) == [], "resilient log entry does not store actor PII"
    assert value_referenced(actor.pk, resilient_log_entry), "resilient log entry references actor PK"
    assert user_pii_leaks(user, resilient_log_entry) == [], "resilient log entry does not store user PII"
    assert value_referenced(user.pk, resilient_log_entry), "resilient log entry references user PK"


@pytest.mark.django_db
def test__object_deleted_resilient_logger_does_not_leak_actor_pii(actor, additional_sign_plan):
    with set_actor(actor):
        additional_sign_plan.delete()
    auditlog_entry = LogEntry.objects.get_for_model(AdditionalSignPlan).filter(action=LogEntry.Action.DELETE).last()
    resilient_log_entry = DjangoAuditLogSourceEntry(auditlog_entry)
    assert user_pii_leaks(actor, resilient_log_entry) == [], "resilient log entry does not store actor PII"
    assert value_referenced(actor.pk, resilient_log_entry), "resilient log entry references actor PK"


# M2M tests


@pytest.mark.django_db
@pytest.mark.parametrize(
    "get_related_obj, actor_relation, related_relation",
    [
        (OperationalAreaFactory, "operational_areas", "users"),
        (ResponsibleEntityFactory, "responsible_entities", "users"),
        (lambda: Group.objects.create(name="Test group"), "groups", "user_set"),
        (lambda: ADGroup.objects.create(name="Test AD group"), "ad_groups", "user_set"),
        (lambda: Permission.objects.get(codename="add_user"), "user_permissions", "user_set"),
    ],
    ids=["operational_area", "responsible_entity", "group", "ad_group", "user_permission"],
)
def test__m2m_relations_do_not_leak_user_pii(actor, user, get_related_obj, actor_relation, related_relation):
    related_obj = get_related_obj()

    getattr(actor, actor_relation).add(related_obj)
    actor.save()
    auditlog_entry = LogEntry.objects.get_for_object(actor).filter(action=LogEntry.Action.UPDATE).last()
    resilient_log_entry = DjangoAuditLogSourceEntry(auditlog_entry)
    assert user_pii_leaks(actor, resilient_log_entry) == [], "log entry does not store actor PII"
    assert value_referenced(actor.pk, resilient_log_entry), "log entry references actor PK"
    assert value_referenced(related_obj, resilient_log_entry), "log entry references related object"

    getattr(related_obj, related_relation).add(user)
    related_obj.save()
    auditlog_entry = LogEntry.objects.get_for_object(related_obj).filter(action=LogEntry.Action.UPDATE).last()
    resilient_log_entry = DjangoAuditLogSourceEntry(auditlog_entry)
    assert user_pii_leaks(user, resilient_log_entry) == [], "log entry does not store user PII"
    assert value_referenced(user.pk, resilient_log_entry), "log entry references user PK"
    assert value_referenced(related_obj, resilient_log_entry), "log entry references related object"
