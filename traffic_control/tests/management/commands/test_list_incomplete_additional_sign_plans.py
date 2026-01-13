from io import StringIO

import pytest
from django.core.management import call_command

from traffic_control.tests.factories import AdditionalSignPlanFactory, TrafficSignPlanFactory


@pytest.mark.django_db
def test_validation_success():
    """Case 1: All objects are valid. Command should report success."""

    t1 = TrafficSignPlanFactory()
    t2 = TrafficSignPlanFactory()
    AdditionalSignPlanFactory(parent=t1)
    AdditionalSignPlanFactory(parent=t2)

    out = StringIO()
    call_command("list_incomplete_additional_sign_plans", stdout=out)
    output = out.getvalue()

    assert "All 2 objects passed validation" in output
    assert "failed validation" not in output


@pytest.mark.django_db
def test_validation_failure_reporting():
    """Case 2: Objects bypass .clean() via .update(). Command should report failure."""

    t1 = TrafficSignPlanFactory()
    t2 = TrafficSignPlanFactory()
    AdditionalSignPlanFactory(parent=t1)
    bogus = AdditionalSignPlanFactory(
        parent=t2,
        # Simplest condition to failure: (missing_content is True) and (content_s is not None)
        missing_content=True,
        content_s='{"fail?": True}',
    )

    out = StringIO()
    err = StringIO()
    call_command("list_incomplete_additional_sign_plans", stdout=out, stderr=err)
    output_stdout = out.getvalue()
    output_stderr = err.getvalue()

    # Check if the failure was caught
    assert "Validation complete. 1 objects failed out of 2." in output_stdout
    assert f"{bogus} failed validation" in output_stderr
