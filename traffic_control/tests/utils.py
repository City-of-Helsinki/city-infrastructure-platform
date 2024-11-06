class DummyRequestForAxes:
    def __init__(self, locked_out=False, meta=None, headers=None):
        self.axes_locked_out = False
        self.META = meta or {}
        self.headers = headers or {}
