from typing import Any

import pytest
from auditlog.context import set_actor
from auditlog.models import LogEntry
from django.contrib.auth.models import Group, Permission
from helusers.models import ADGroup

from traffic_control.models import TrafficSignReal
from traffic_control.tests.factories import (
    OperationalAreaFactory,
    ResponsibleEntityFactory,
    TrafficSignRealFactory,
    UserFactory,
)
from users.models import User


@pytest.fixture
def actor():
    return UserFactory(
        email="erika.esimerkinen@example.com",
        first_name="Erika",
        last_name="Esimerkinen",
        username="erika_esimerkinen",
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
def traffic_sign_real(actor):
    with set_actor(actor):
        return TrafficSignRealFactory(
            created_by=actor,
            updated_by=actor,
        )


# Utility checks
# NOTE (2026-04-30 thiago)
# These checks merely check for the presence of PII data in the log entries, they don't otherwise analyze whether such
# data is placed in the correct fields, since that kind of check belongs in django-auditlog tests or other application
# tests about logs being written correctly.


def user_pii_leaks(user: User | UserFactory, logentry: LogEntry):
    """
    Checks for user PII leaks in a LogEntry object
    """
    leaks = []
    for user_field in ["email", "first_name", "last_name"]:
        for logentry_field in logentry.__dict__:
            # NOTE (2026-04-30 thiago)
            # This check is unreliable in cases such as very short strings or None values, our test strings are long
            # enough, plus "leaking" of None values is irrelevant for the tests.
            if str(getattr(user, user_field)) in str(getattr(logentry, logentry_field)):
                leaks.append(f"Actor {user_field} found in LogEntry '{logentry_field}' field")
    return leaks


def value_referenced(value: Any, logentry: LogEntry):
    """
    Checks for references to a particular value in a LogEntry object
    """
    data_str = str(logentry.__dict__)
    return str(value) in data_str


# Operations on User objects


@pytest.mark.django_db
def test__user_created_auditlog_does_not_leak_user_pii(user):
    logentries = LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.CREATE)
    assert logentries.count() == 1
    assert user_pii_leaks(user, logentries[0]) == [], "log entry does not store user PII"
    assert value_referenced(user.pk, logentries[0]), "log entry references user PK"


@pytest.mark.django_db
def test__user_updated_auditlog_does_not_leak_user_pii(user):
    user.email = "xavier.example@example.com"
    user.first_name = "Xavier"
    user.last_name = "Example"
    user.username = "xavier_example"
    user.save()
    logentries = LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.UPDATE)
    assert logentries.count() == 1
    assert user_pii_leaks(user, logentries[0]) == [], "log entry does not store user PII"
    assert value_referenced(user.pk, logentries[0]), "log entry references user PK"


@pytest.mark.django_db
def test__user_deleted_auditlog_does_not_leak_user_pii(user):
    user.delete()
    logentries = LogEntry.objects.get_for_model(User).filter(action=LogEntry.Action.DELETE)
    assert logentries.count() == 1
    assert user_pii_leaks(user, logentries[0]) == [], "log entry does not store user PII"
    assert value_referenced(user.pk, logentries[0]), "log entry references user PK"


# Operations on other objects


@pytest.mark.django_db
def test__object_created_does_not_leak_actor_pii(actor, traffic_sign_real):
    logentries = LogEntry.objects.get_for_object(traffic_sign_real).filter(action=LogEntry.Action.CREATE)
    assert logentries.count() == 1
    assert user_pii_leaks(actor, logentries[0]) == [], "log entry does not store actor PII"
    assert value_referenced(actor.pk, logentries[0]), "log entry references actor PK"


@pytest.mark.django_db
def test__object_updated_does_not_leak_actor_pii(actor, user, traffic_sign_real):
    with set_actor(actor):
        traffic_sign_real.updated_by = user
        traffic_sign_real.save()

    logentries = LogEntry.objects.get_for_object(traffic_sign_real).filter(action=LogEntry.Action.UPDATE)
    assert logentries.count() == 1
    assert user_pii_leaks(actor, logentries[0]) == [], "log entry does not store actor PII"
    assert value_referenced(actor.pk, logentries[0]), "log entry references actor PK"
    assert user_pii_leaks(user, logentries[0]) == [], "log entry does not store user PII"
    assert value_referenced(user.pk, logentries[0]), "log entry references user PK"


@pytest.mark.django_db
def test__object_deleted_does_not_leak_actor_pii(actor, traffic_sign_real):
    with set_actor(actor):
        traffic_sign_real.delete()

    logentries = LogEntry.objects.get_for_model(TrafficSignReal).filter(action=LogEntry.Action.DELETE)
    assert logentries.count() == 1
    assert user_pii_leaks(actor, logentries[0]) == [], "log entry does not store actor PII"
    assert value_referenced(actor.pk, logentries[0]), "log entry references actor PK"


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
    logentries = LogEntry.objects.get_for_object(actor).filter(action=LogEntry.Action.UPDATE)
    assert logentries.count() == 1
    assert user_pii_leaks(actor, logentries[0]) == [], "log entry does not store actor PII"
    assert value_referenced(actor.pk, logentries[0]), "log entry references actor PK"
    assert value_referenced(related_obj, logentries[0]), "log entry references related object"

    getattr(related_obj, related_relation).add(user)
    related_obj.save()
    logentries = LogEntry.objects.get_for_object(related_obj).filter(action=LogEntry.Action.UPDATE)
    assert logentries.count() == 1
    assert user_pii_leaks(user, logentries[0]) == [], "log entry does not store user PII"
    assert value_referenced(user.pk, logentries[0]), "log entry references user PK"
    assert value_referenced(related_obj, logentries[0]), "log entry references related object"
