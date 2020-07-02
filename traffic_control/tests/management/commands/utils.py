from unittest.mock import mock_open as _mock_open


def mock_open(mock=None, read_data=""):
    # mock_open does not implement required dunder methods
    # in order to be consumable by csv.reader. There's an
    # open issue regarding this: https://bugs.python.org/issue21258
    m = _mock_open(mock, read_data=read_data)
    m.return_value.__iter__ = lambda f: f
    m.return_value.__next__ = lambda f: next(iter(f.readline, ""))
    return m
