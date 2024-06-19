from django.contrib.auth.middleware import get_user
from django.utils.functional import SimpleLazyObject
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


def _get_user(drf_auth_class, request):
    user = get_user(request)
    if user.is_authenticated:
        return user
    try:
        user_tuple = drf_auth_class().authenticate(request)
        if user_tuple:
            user = user_tuple[0]
    except AuthenticationFailed:
        pass
    return user


def get_user_token(request):
    return _get_user(TokenAuthentication, request)


def get_user_basic(request):
    return _get_user(BasicAuthentication, request)


def get_basic_or_token_user(request):
    token_user = get_user_token(request)
    basic_user = get_user_basic(request)
    return token_user if token_user.is_authenticated else basic_user


class DRFCustomAuthMiddleware:
    """Middleware for saving authentication info to request when DRF authentication methods are used.
    This is a workaround for auditlog bug: https://github.com/jazzband/django-auditlog/issues/115 which actually is
    a caused by design in DRF: authentication is done in view level.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        request.user = SimpleLazyObject(lambda: get_basic_or_token_user(request))
        return self.get_response(request)
