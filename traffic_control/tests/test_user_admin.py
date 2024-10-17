import pytest
from django.test import Client, override_settings
from django.urls import reverse

TOO_CLOSE_TO_USERNAME = "Salasana on liian lähellä kohdetta käyttäjätunnus."
TOO_SHORT = "Tämä salasana on liian lyhyt. Sen tulee sisältää ainakin 12 merkkiä."
TOO_COMMON = "Tämä salasana on liian yleinen."
NUMBER_MISSING = "Password must contain at least 1 number."
UPPERCASE_MISSING = "Password must contain at least 1 uppercase character."
LOWERCASE_MISSING = "Password must contain at least 1 lowercase character."
SPECIAL_CHAR_MISSING = "Password must contain at least 1 special character ( !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~)."


settings_overrides = override_settings(
    STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
)


def setup_module():
    settings_overrides.enable()


def teardown_module():
    settings_overrides.disable()


@pytest.mark.parametrize(
    "username,password,expected_msgs",
    (
        (
            "test",
            "test",
            [TOO_CLOSE_TO_USERNAME, TOO_SHORT, TOO_COMMON, NUMBER_MISSING, UPPERCASE_MISSING, SPECIAL_CHAR_MISSING],
        ),
        (
            "test",
            "TEST",
            [TOO_CLOSE_TO_USERNAME, TOO_SHORT, TOO_COMMON, NUMBER_MISSING, LOWERCASE_MISSING, SPECIAL_CHAR_MISSING],
        ),
        (
            "test",
            "Kall3Kall3!",
            [TOO_SHORT],
        ),
        (
            "test",
            "Kall3Kall312",
            [SPECIAL_CHAR_MISSING],
        ),
        (
            "test",
            "kall3kall31!",
            [UPPERCASE_MISSING],
        ),
        (
            "test",
            "KALL3KALL31!",
            [LOWERCASE_MISSING],
        ),
        (
            "test",
            "Kall3Kall3!12",
            [],
        ),
    ),
)
@pytest.mark.django_db
def test__create_user_password_validation(client: Client, admin_user, username, password, expected_msgs):
    client.force_login(admin_user)
    response = client.post(
        reverse("admin:users_user_add"), {"username": username, "password": password, "password2": password}
    )

    assert response.status_code == 200

    for msg in expected_msgs:
        assert msg in response.context.get("errors")[1]
