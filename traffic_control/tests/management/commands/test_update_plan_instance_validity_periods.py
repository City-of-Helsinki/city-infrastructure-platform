import datetime

import pytest
from django.core.management import call_command

from traffic_control.mixins.models import ValidityPeriodModel
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    BarrierPlanFactory,
    MountPlanFactory,
    RoadMarkingPlanFactory,
    SignpostPlanFactory,
    TrafficLightPlanFactory,
    TrafficSignPlanFactory,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory_cls",
    [
        BarrierPlanFactory,
        MountPlanFactory,
        RoadMarkingPlanFactory,
        SignpostPlanFactory,
        TrafficLightPlanFactory,
        TrafficSignPlanFactory,
        AdditionalSignPlanFactory,
    ],
)
def test_update_plan_instance_validity_periods(factory_cls):
    model_cls = factory_cls._meta.model
    if not issubclass(model_cls, ValidityPeriodModel):
        pytest.skip(f"{model_cls.__name__} does not inherit from ValidityPeriodModel")
    date_start = datetime.date(2024, 1, 1)
    date_decision = datetime.date(2024, 6, 1)
    instance = factory_cls(validity_period_start=date_start)
    plan = instance.plan
    plan.decision_date = date_decision
    plan.save(update_fields=["decision_date"])
    assert instance.validity_period_start != plan.decision_date

    call_command("update_plan_instance_validity_periods")

    instance.refresh_from_db()
    assert instance.validity_period_start == plan.decision_date
