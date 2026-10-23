import pytest

from users.utils import get_system_user


@pytest.mark.django_db
def test_get_system_user_is_not_activated_and_not_staff():
    user = get_system_user()
    assert user.is_active is False
    assert user.is_staff is False
