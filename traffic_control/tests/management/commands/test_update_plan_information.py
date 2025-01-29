import datetime
import os
from tempfile import TemporaryDirectory

import pytest
from django.core.management import call_command

from traffic_control.models import Plan
from traffic_control.tests.factories import PlanFactory

BASE_PATH = os.path.dirname(__file__)
TEST_FILES_DIR = os.path.join(BASE_PATH, "../../test_datas/plan_update")


def _create_db_entries():
    """Create existing Plan's to database. Currently just one on purpose that matches one row in the test csv"""
    return PlanFactory(decision_id="EXISTS1")


@pytest.mark.django_db
def test__update_plan_information():
    original_plan = _create_db_entries()
    with TemporaryDirectory() as tempdir:
        call_command(
            "update_plan_information",
            plan_file=os.path.join(TEST_FILES_DIR, "basic_update_data.csv"),
            output_dir=tempdir,
        )

    updated_plan = Plan.objects.get(pk=original_plan.pk)
    # check that not all fields are updated
    assert updated_plan.created_by == original_plan.created_by
    assert updated_plan.updated_by == original_plan.updated_by
    assert updated_plan.name == original_plan.name
    assert updated_plan.location == original_plan.location
    assert updated_plan.derive_location == original_plan.derive_location
    assert updated_plan.is_active == original_plan.is_active
    assert updated_plan.source_id == original_plan.source_id
    assert updated_plan.source_name == original_plan.source_name
    # check that decision_date, diary_number, drawing_numbers and decision_url are updated
    assert updated_plan.decision_date == datetime.date(2012, 1, 13)
    assert updated_plan.diary_number == "DN1"
    assert updated_plan.drawing_numbers == ["6103-1", "6102-1"]
    assert updated_plan.decision_url == "https://dummyurl"
