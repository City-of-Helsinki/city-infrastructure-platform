import pytest
from django.core.management import call_command

from traffic_control.tests.factories import PlanFactory
from users.utils import get_system_user

EXPECTED_URL = "https://paatokset.hel.fi/fi/asia/HEL-2024-013184"
EXISTING_URL = "https://example.com/decision"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "plan_kwargs, command_kwargs, expected_url",
    (
        ({"decision_url": ""}, {}, EXPECTED_URL),
        ({"decision_url": None}, {}, EXPECTED_URL),
        ({"decision_url": EXISTING_URL}, {}, EXISTING_URL),
        ({"decision_url": EXISTING_URL}, {"force": True}, EXPECTED_URL),
        ({"decision_url": "", "diary_number": None}, {"force": True}, ""),
        ({"decision_url": "", "is_active": False}, {"force": True}, ""),
        ({"decision_url": ""}, {"dry_run": True, "force": False}, ""),
        ({"decision_url": ""}, {"dry_run": True, "force": True}, ""),
    ),
    ids=[
        "fills_empty_decision_url",
        "fills_null_decision_url",
        "does_not_overwrite_existing_url",
        "force_overwrites_existing_url",
        "plan_without_diary_number_is_skipped",
        "soft_deleted_plan_is_skipped",
        "dry_run_does_not_update",
        "dry_run_with_force_does_not_update",
    ],
)
def test__populate_plan_decision_urls(plan_kwargs, command_kwargs, expected_url):
    plan = PlanFactory(**{"diary_number": "HEL 2024-013184", **plan_kwargs})
    original_updated_by = plan.updated_by
    plan_is_updated = plan.decision_url != expected_url

    call_command("populate_plan_decision_urls", **command_kwargs)

    plan.refresh_from_db()
    assert plan.decision_url == expected_url
    assert plan.updated_by == (get_system_user() if plan_is_updated else original_updated_by)
