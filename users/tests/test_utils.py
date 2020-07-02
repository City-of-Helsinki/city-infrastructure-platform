from django.test import TestCase

from users.utils import get_system_user


class GetSystemUserTestCase(TestCase):
    def test_get_system_user_is_not_activated_and_not_staff(self):
        user = get_system_user()
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)
