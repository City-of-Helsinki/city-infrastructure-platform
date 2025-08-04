import pytest
from django.core.management import call_command

from traffic_control.tests.factories import AdditionalSignRealFactory


@pytest.mark.django_db
def test_print_target_model_check():
    """Pretty much just dummy test to check that management command does not crash
    No check to the actual stdout print is done.
    """
    AdditionalSignRealFactory(device_type__target_model=None)
    call_command("print_target_model_check")
