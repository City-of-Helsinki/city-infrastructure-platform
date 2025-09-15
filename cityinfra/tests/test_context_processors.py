import os

import pytest
from django.test import RequestFactory

from cityinfra.context_processors import git_version


@pytest.fixture
def req():
    """Returns a RequestFactory instance."""
    return RequestFactory().get("/")


@pytest.mark.parametrize(
    "env_value, expected",
    [
        # Test case 1: VERSION environment variable is set
        ("a1b2c3d4e5f6g7h8i9j0", "a1b2c3d4e5f6g7h8i9j0"),
        # Test case 2: VERSION environment variable is not set
        (None, "not found"),
    ],
)
def test_git_version_context_processor(req, env_value, expected):
    """
    Tests the git_version context processor with a set and unset
    VERSION environment variable.
    """
    # Clean up the environment before each run to prevent side effects
    if "VERSION" in os.environ:
        del os.environ["VERSION"]

    # Set the environment variable for the specific test case if a value is provided
    if env_value is not None:
        os.environ["VERSION"] = env_value

    result = git_version(req)

    # Assert that the function returns the correct value
    assert result["GIT_VERSION"] == expected
