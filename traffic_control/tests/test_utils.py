import pytest

from traffic_control.tests.utils import DummyRequestForAxes
from traffic_control.utils import get_client_ip


@pytest.mark.parametrize(
    "address,expected,in_header",
    (
        ("1.12.123.1", "1.12.123.1", True),
        ("1.12.123.1:80", "1.12.123.1", True),
        ("1.12.123.1", "1.12.123.1", False),
        ("[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:80", "2001:0db8:85a3:0000:0000:8a2e:0370:7334", True),
        ("2001:0db8:85a3:0000:0000:8a2e:0370:7334", "2001:0db8:85a3:0000:0000:8a2e:0370:7334", True),
        ("2001:0db8:85a3:0000:0000:8a2e:0370:7334", "2001:0db8:85a3:0000:0000:8a2e:0370:7334", False),
    ),
)
def test_client_ip(address, expected, in_header):
    meta = {"REMOTE_ADDR": address} if not in_header else {}
    headers = {"x-forwarded-for": address} if in_header else {}
    dummy_request = DummyRequestForAxes(meta=meta, headers=headers)
    assert get_client_ip(dummy_request) == expected
