"""
Django settings for city-infrastructure-platform project.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os

import environ
import sentry_sdk
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from helusers.defaults import SOCIAL_AUTH_PIPELINE  # noqa: F401
from sentry_sdk.integrations.django import DjangoIntegration

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

BASE_DIR = checkout_dir()

env = environ.Env(
    DEBUG=(bool, False),
    ENVIRONMENT_NAME=(str, ""),
    SECRET_KEY=(str, ""),
    VAR_ROOT=(str, default_var_root),
    HOST=(str, "localhost"),
    HOST_PUBLIC=(str, ""),
    ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGIN_REGEXES=(list, []),
    TRUST_X_FORWARDED_HOST=(bool, False),
    DATABASE_URL=(
        str,
        "postgis:///city-infrastructure-platform",
    ),
    CACHE_URL=(str, "locmemcache://"),
    EMAIL_URL=(str, "consolemail://"),
    SENTRY_DSN=(str, ""),
    SENTRY_DEBUG=(bool, False),
    VERSION=(str, ""),
    OPENSHIFT_DEPLOYMENT=(bool, False),
    AZURE_ACCOUNT_KEY=(str, False),
    AZURE_CONTAINER=(str, False),
    AZURE_ACCOUNT_NAME=(str, False),
    OIDC_AUTHENTICATION_ENABLED=(bool, True),
    SOCIAL_AUTH_TUNNISTAMO_KEY=(str, None),
    SOCIAL_AUTH_TUNNISTAMO_SECRET=(str, None),
    OIDC_API_TOKEN_AUTH_AUDIENCE=(str, None),
    OIDC_API_TOKEN_AUTH_ISSUER=(str, None),
    TOKEN_AUTH_MAX_TOKEN_AGE=(int, 600),
    OIDC_ENDPOINT=(str, None),
    HELUSERS_ADGROUPS_CLAIM=(str, "groups"),
    LOGGING_AUTH_DEBUG=(bool, False),
    BASEMAP_SOURCE_URL=(str, "https://kartta.hel.fi/ws/geoserver/avoindata/wms"),
    STATIC_URL=(str, "/static/"),
    MEDIA_URL=(str, "/media/"),
)

if os.path.exists(env_file):
    env.read_env(env_file)

SESSION_SERIALIZER = "helusers.sessions.TunnistamoOIDCSerializer"

SOCIAL_AUTH_TUNNISTAMO_KEY = env("SOCIAL_AUTH_TUNNISTAMO_KEY")
SOCIAL_AUTH_TUNNISTAMO_SECRET = env("SOCIAL_AUTH_TUNNISTAMO_SECRET")
HELUSERS_ADGROUPS_CLAIM = env("HELUSERS_ADGROUPS_CLAIM")

SOCIAL_AUTH_ID_TOKEN_IN_END_SESSION = False

if env("OIDC_ENDPOINT"):
    SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT = env("OIDC_ENDPOINT")

OIDC_API_TOKEN_AUTH = {
    "AUDIENCE": env("OIDC_API_TOKEN_AUTH_AUDIENCE"),
    "ISSUER": env("OIDC_API_TOKEN_AUTH_ISSUER"),
}

# General settings
DEBUG = env("DEBUG")
OIDC_AUTHENTICATION_ENABLED = env("OIDC_AUTHENTICATION_ENABLED")
ENVIRONMENT_NAME = env("ENVIRONMENT_NAME")
SECRET_KEY = env("SECRET_KEY")
if DEBUG and not SECRET_KEY:
    SECRET_KEY = "xxx"

HOSTNAME = env("HOST_PUBLIC") or env("HOST")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

if OIDC_AUTHENTICATION_ENABLED and (
    not SOCIAL_AUTH_TUNNISTAMO_KEY
    or not SOCIAL_AUTH_TUNNISTAMO_SECRET
    or not OIDC_API_TOKEN_AUTH["AUDIENCE"]
    or not OIDC_API_TOKEN_AUTH["ISSUER"]
):
    raise ImproperlyConfigured("Authentication not configured properly")

CACHES = {"default": env.cache()}
vars().update(env.email_url())  # EMAIL_BACKEND etc.

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "timestamped_named": {
            "format": "%(asctime)s %(name)s %(levelname)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "timestamped_named",
        },
        # Just for reference, not used
        "blackhole": {"class": "logging.NullHandler"},
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "helusers": {
            "handlers": ["console"],
            "level": "DEBUG" if env("LOGGING_AUTH_DEBUG") else "INFO",
            "propagate": False,
        },
    },
}

# Application definition
DJANGO_APPS = [
    "social_django",
    "helusers.apps.HelusersConfig",
    "helusers.apps.HelusersAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.admindocs",
]
THIRD_PARTY_APPS = [
    "django_extensions",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "drf_spectacular",
    "django_filters",
    "auditlog",
    "colorfield",
    "import_export",
    "gisserver",
    "mptt",
]
LOCAL_APPS = [
    "users.apps.UsersConfig",
    "traffic_control.apps.TrafficControlConfig",
    "city_furniture.apps.CityFurnitureConfig",
    "map.apps.MapConfig",
    "city_infra_instructions.apps.CityInfraInstructionsConfig",
]
INSTALLED_APPS = LOCAL_APPS + DJANGO_APPS + THIRD_PARTY_APPS

AUTHENTICATION_BACKENDS = (
    "helusers.tunnistamo_oidc.TunnistamoOIDCAuth",
    "django.contrib.auth.backends.ModelBackend",
)

AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/admin/login/"
SOCIAL_AUTH_TUNNISTAMO_AUTH_EXTRA_ARGUMENTS = {"ui_locales": "fi"}
WAGTAIL_SITE_NAME = _("City Infrastructure Platform")

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "drf_custom_auth.middleware.DRFCustomAuthMiddleware",
    "auditlog_custom.middleware.AuditlogMiddleware",
]

ROOT_URLCONF = "cityinfra.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [checkout_dir("cityinfra/templates"), checkout_dir("map-view/build")],
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

WSGI_APPLICATION = "cityinfra.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/
LANGUAGE_CODE = "fi"
LANGUAGES = [("fi", _("Finnish")), ("en", _("English"))]
TIME_ZONE = "Europe/Helsinki"
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [
    "./locale",
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
var_root = env.path("VAR_ROOT")
STATIC_ROOT = var_root("static")
MEDIA_ROOT = var_root("media")
STATIC_URL = env("STATIC_URL")
MEDIA_URL = env("MEDIA_URL")
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
}
STATICFILES_DIRS = [checkout_dir("map-view/build/static")]

# Whether to trust X-Forwarded-Host headers for all purposes
# where Django would need to make use of its own hostname
# fe. generating absolute URLs pointing to itself
# Most often used in reverse proxy setups
USE_X_FORWARDED_HOST = env("TRUST_X_FORWARDED_HOST")

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "helusers.oidc.ApiTokenAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "EXCEPTION_HANDLER": "cityinfra.exceptions.cityinfra_exception_handler",
    "PAGE_SIZE": 20,
    "OIDC_LEEWAY": env("TOKEN_AUTH_MAX_TOKEN_AGE"),
    "GROUP_CLAIM_NAME": "groups",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

SPECTACULAR_SETTINGS = {
    "COMPONENT_SPLIT_REQUEST": True,
    "POSTPROCESSING_HOOKS": [
        "traffic_control.schema.process_enum_values",
    ],
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/v1",
    "TITLE": "City Infrastructure Platform REST API",
    "VERSION": "v1",
    "LICENSE": {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    "DESCRIPTION": checkout_dir.file("cityinfra/openapi.md").read(),
}

# django-cors
if DEBUG:
    CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOWED_ORIGIN_REGEXES = env("CORS_ALLOWED_ORIGIN_REGEXES")

# OpenShift-specific configuration
OPENSHIFT_DEPLOYMENT = env.bool("OPENSHIFT_DEPLOYMENT")
if OPENSHIFT_DEPLOYMENT:
    # Use Azure Storage Container as file storage in OpenShift deployment
    STORAGES["default"]["BACKEND"] = "storages.backends.azure_storage.AzureStorage"
    AZURE_ACCOUNT_NAME = env.str("AZURE_ACCOUNT_NAME")
    AZURE_CONTAINER = env.str("AZURE_CONTAINER")
    AZURE_ACCOUNT_KEY = env.str("AZURE_ACCOUNT_KEY")

# Sentry-SDK
SENTRY_DSN = env.str("SENTRY_DSN")
SENTRY_DEBUG = env.bool("SENTRY_DEBUG")
VERSION = env.str("VERSION")
if SENTRY_DSN:
    sentry_sdk.init(dsn=SENTRY_DSN, integrations=[DjangoIntegration()], release=VERSION)

# Custom settings
SRID = 3879  # the spatial reference id used for geometries

BASEMAP_SOURCE_URL = env.str("BASEMAP_SOURCE_URL")

# Import / Export
IMPORT_EXPORT_USE_TRANSACTIONS = True
# Require view permission even to export template
IMPORT_EXPORT_EXPORT_PERMISSION_CODE = "view"

# WFS
GISSERVER_USE_DB_RENDERING = False

# Virus scan
CLAMAV_BASE_URL = env.str("CLAMAV_BASE_URL", "http://localhost:3030")

DEBUG_TOOLBAR = False
if DEBUG:
    try:
        import debug_toolbar  # noqa

        DEBUG_TOOLBAR = True
    except ImportError:
        pass

    if DEBUG_TOOLBAR:
        INSTALLED_APPS.append("debug_toolbar")
        MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

        import socket

        try:
            _, _, ips = socket.gethostbyname_ex(socket.gethostname())
            INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1"]
        except Exception:
            INTERNAL_IPS = ["127.0.0.1", "localhost"]
