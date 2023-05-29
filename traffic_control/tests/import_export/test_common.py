from uuid import UUID

import pytest

from traffic_control.resources.common import UUIDWidget

uuid = UUID("09e15054-c4f8-417e-9d21-8d0ff23ec743")
uuid2 = UUID("4372e0ba-5bf2-46bf-ab33-6ffe7966d339")


@pytest.mark.parametrize(
    ("input", "expected"),
    (
        (None, None),
        ("", None),
        (uuid, uuid),
        (str(uuid2), uuid2),
    ),
)
def test__uuid_widget__clean__valid(input, expected):
    widget = UUIDWidget()
    cleaned = widget.clean(input)
    assert cleaned == expected


@pytest.mark.parametrize(
    "input",
    (
        0,
        1,
        True,
        False,
        "word",
        "two words",
    ),
)
def test__uuid_widget__clean__invalid(input):
    widget = UUIDWidget()
    with pytest.raises(ValueError):
        widget.clean(input)
