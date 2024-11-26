from django.conf import settings

MIN_X, MIN_Y, MAX_X, MAX_Y = settings.SRID_BOUNDARIES.get(settings.SRID)


class DummyRequestForAxes:
    def __init__(self, locked_out=False, meta=None, headers=None):
        self.axes_locked_out = False
        self.META = meta or {}
        self.headers = headers or {}
