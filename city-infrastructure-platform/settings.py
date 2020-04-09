"""
Django settings for city-infrastructure-platform project.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

import environ
import sentry_sdk
from django.utils.translation import gettext_lazy as _  # NOQA
from sentry_sdk.integrations.django import DjangoIntegration

from .utils import git_version

# Set up .env file
checkout_dir = environ.Path(__file__) - 2
assert os.path.exists(checkout_dir("manage.py"))

parent_dir = checkout_dir.path("..")
if parent_dir() != "/" and os.path.isdir(parent_dir("etc")):
    env_file = parent_dir("etc/env")
    default_var_root = parent_dir("var")
else:
    env_file = checkout_dir(".env")
    default_var_root = checkout_dir("var")

env = environ.Env(
    DEBUG=(bool, False),
    TIER=(str, "dev"),  # one of: prod, qa, stage, test, dev
    SECRET_KEY=(str, ""),
    VAR_ROOT=(str, default_var_root),
    ALLOWED_HOSTS=(list, []),
    DATABASE_URL=(str, "postgis:///city-infrastructure-platform",),
    CACHE_URL=(str, "locmemcache://"),
    EMAIL_URL=(str, "consolemail://"),
    SENTRY_DSN=(str, ""),
    AZURE_DEPLOYMENT=(bool, False),
    AZURE_ACCOUNT_KEY=(str, False),
    AZURE_CONTAINER=(str, False),
    AZURE_ACCOUNT_NAME=(str, False),
)
if os.path.exists(env_file):
    env.read_env(env_file)

# General settings
DEBUG = env.bool("DEBUG")
TIER = env.str("TIER")
SECRET_KEY = env.str("SECRET_KEY")
if DEBUG and not SECRET_KEY:
    SECRET_KEY = "xxx"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

CACHES = {"default": env.cache()}
vars().update(env.email_url())  # EMAIL_BACKEND etc.

# Application definition
DJANGO_APPS = [
    "helusers",
    "social_django",
    "helusers.apps.HelusersAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
]
THIRD_PARTY_APPS = [
    "django_extensions",
    "rest_framework",
    "corsheaders",
    "drf_yasg",
    "django_filters",
    "auditlog",
]
LOCAL_APPS = ["users.apps.UsersConfig", "traffic_control.apps.TrafficControlConfig"]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

AUTHENTICATION_BACKENDS = (
    # "helusers.tunnistamo_oidc.TunnistamoOIDCAuth", # disable OIDC-provider for now
    "django.contrib.auth.backends.ModelBackend",
)

AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/admin/login/"
SOCIAL_AUTH_TUNNISTAMO_AUTH_EXTRA_ARGUMENTS = {"ui_locales": "fi"}
WAGTAIL_SITE_NAME = _("City Infrastructure Platform Administration")

TUNNISTAMO_BASE_URL = "https://api.hel.fi/sso"
SOCIAL_AUTH_TUNNISTAMO_KEY = "12082ae5-f104-45f3-990e-a030e9bcb60"
SOCIAL_AUTH_TUNNISTAMO_SECRET = "abcd1234abcd1234abcd1234abcd1234"
SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT = TUNNISTAMO_BASE_URL + "/openid"

SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"

MIDDLEWARE = [
    "deployment.middleware.HealthCheckMiddleware",
    "azure_client_ip.middleware.AzureClientIPMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
]

ROOT_URLCONF = "city-infrastructure-platform.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "city-infrastructure-platform.wsgi.application"

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/
LANGUAGE_CODE = "fi"
LANGUAGES = [("fi", _("Finnish")), ("en", _("English"))]
TIME_ZONE = "Europe/Helsinki"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

var_root = env.path("VAR_ROOT")
MEDIA_ROOT = var_root("media")
STATIC_ROOT = var_root("static")
MEDIA_URL = "/media/"
STATIC_URL = "/static/"
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "helusers.oidc.ApiTokenAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "PAGE_SIZE": 10,
}

# django-cors
if DEBUG:
    CORS_ORIGIN_ALLOW_ALL = True

# Azure CLIENT_IP middleware
AZURE_DEPLOYMENT = env.bool("AZURE_DEPLOYMENT")

if AZURE_DEPLOYMENT:
    AZURE_ACCOUNT_KEY = env.str("AZURE_ACCOUNT_KEY")
    AZURE_CONTAINER = env.str("AZURE_CONTAINER")
    AZURE_ACCOUNT_NAME = env.str("AZURE_ACCOUNT_NAME")
    DEFAULT_FILE_STORAGE = "storages.backends.azure_storage.AzureStorage"

# Sentry-SDK
SENTRY_DSN = env.str("SENTRY_DSN")
VERSION = git_version()
if SENTRY_DSN:
    sentry_sdk.init(dsn=SENTRY_DSN, integrations=[DjangoIntegration()], release=VERSION)

# Custom settings
SRID = 3879  # the spatial reference id used for geometries
