from unittest.mock import MagicMock

import pytest
from django.test import RequestFactory

from traffic_control.permissions import IsAdminUserOrReadOnly

mock_view = MagicMock()
mock_user = MagicMock()


@pytest.mark.parametrize(
    "method,is_staff,expected",
    [
        ["get", False, True],
        ["get", True, True],
        ["head", False, True],
        ["head", True, True],
        ["options", False, True],
        ["options", True, True],
        ["post", False, False],
        ["post", True, True],
        ["patch", False, False],
        ["patch", True, True],
        ["put", False, False],
        ["put", True, True],
    ],
)
def test_is_admin_user_or_read_only(method, is_staff, expected):
    request = RequestFactory().generic(method=method, path="/")
    request.user = mock_user
    request.user.is_staff = is_staff
    assert IsAdminUserOrReadOnly().has_permission(request, mock_view) == expected
