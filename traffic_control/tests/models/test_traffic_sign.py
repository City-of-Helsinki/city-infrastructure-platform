from types import SimpleNamespace

import pytest
from django.contrib.gis.geos import Point

from traffic_control.models import AdditionalSignPlan, AdditionalSignReal, TrafficSignPlan, TrafficSignReal
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    get_owner,
    get_user,
    TrafficControlDeviceTypeFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)
from traffic_control.tests.utils import MIN_X, MIN_Y


@pytest.fixture
def user(db):
    return get_user()


@pytest.fixture(
    params=[
        (TrafficSignPlan, AdditionalSignPlan, TrafficSignPlanFactory, AdditionalSignPlanFactory),
        (TrafficSignReal, AdditionalSignReal, TrafficSignRealFactory, AdditionalSignRealFactory),
    ],
    ids=["plan", "real"],
)
def sign_suite(request, db, settings, user):
    """
    Real / Plan fixtures for main sign, sign class, additional sign class, sign factory, additional sign factory
    """
    model_cls, add_model_cls, factory, add_factory = request.param

    # Handle the fact that Plan needs device_type while Real has legacy_code
    is_plan = model_cls is TrafficSignPlan
    extra_kwargs = {"device_type": TrafficControlDeviceTypeFactory(code="T123")} if is_plan else {"legacy_code": "100"}

    main_sign = factory.create(
        location=Point(MIN_X + 1, MIN_Y + 1, 10, srid=settings.SRID),
        direction=0,
        created_by=user,
        updated_by=user,
        owner=get_owner(),
        **extra_kwargs,
    )

    yield SimpleNamespace(
        main_sign=main_sign,
        model_cls=model_cls,
        add_model_cls=add_model_cls,
        factory=factory,
        add_factory=add_factory,
    )


@pytest.mark.django_db
def test_main_sign_has_additional_signs_return_false(sign_suite):
    assert sign_suite.main_sign.has_additional_signs() is False


@pytest.mark.django_db
def test_main_sign_has_additional_signs_return_true(sign_suite):
    sign_suite.add_factory(parent=sign_suite.main_sign)
    assert sign_suite.main_sign.has_additional_signs() is True


@pytest.mark.django_db
def test_has_additional_signs_return_false_with_soft_deleted_additional_sign(sign_suite, user):
    additional_sign = sign_suite.add_factory(parent=sign_suite.main_sign)
    additional_sign.soft_delete(user)
    assert sign_suite.main_sign.has_additional_signs() is False


@pytest.mark.django_db
def test_queryset_soft_delete_handles_additional_signs(sign_suite, user):
    sign_suite.add_factory(parent=sign_suite.factory.create())
    additional_sign = sign_suite.add_factory(parent=sign_suite.main_sign)
    assert sign_suite.model_cls.objects.count() == 2

    sign_suite.model_cls.objects.filter(pk=sign_suite.main_sign.pk).soft_delete(user)
    sign_suite.main_sign.refresh_from_db()
    additional_sign.refresh_from_db()

    assert sign_suite.main_sign.is_active is False
    assert sign_suite.main_sign.deleted_by == user
    assert additional_sign.is_active is False
    assert additional_sign.deleted_by == user
    assert sign_suite.model_cls.objects.active().count() == 1
    assert sign_suite.add_model_cls.objects.active().count() == 1


@pytest.mark.django_db
def test_soft_delete_without_additional_signs(sign_suite, user):
    sign_suite.main_sign.soft_delete(user)
    sign_suite.main_sign.refresh_from_db()
    assert sign_suite.main_sign.is_active is False


@pytest.mark.django_db
def test_soft_delete_main_traffic_sign_also_soft_delete_additional_sign(sign_suite, user):
    additional_sign = sign_suite.add_factory(parent=sign_suite.main_sign)
    sign_suite.main_sign.soft_delete(user)
    additional_sign.refresh_from_db()
    assert additional_sign.is_active is False
    assert additional_sign.deleted_by == user
