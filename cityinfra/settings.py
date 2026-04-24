"""
Django settings for city-infrastructure-platform project.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
import sys

import environ
import sentry_sdk
from django.conf.global_settings import MIGRATION_MODULES
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
    # --- Core & General ---
    # https://docs.djangoproject.com/en/5.2/ref/settings/
    BASE_URL=(str, "http://127.0.0.1:8000"),
    DEBUG=(bool, False),  # https://docs.djangoproject.com/en/5.2/ref/settings/#debug
    ENVIRONMENT_NAME=(str, ""),  # e.g., "development", "staging", "production"
    SECRET_KEY=(str, ""),  # https://docs.djangoproject.com/en/5.2/ref/settings/#secret-key
    VAR_ROOT=(str, default_var_root),  # Composes Django's STATIC_ROOT and MEDIA_ROOT
    VERSION=(str, ""),  # Service version
    # --- Network, Hosts & CORS ---
    ALLOWED_HOSTS=(list, []),  # https://docs.djangoproject.com/en/5.2/ref/settings/#allowed-hosts
    # https://github.com/adamchainz/django-cors-headers#cors_allowed_origin_regexes-sequencestr--patternstr
    CORS_ALLOWED_ORIGIN_REGEXES=(list, []),
    HOST=(str, "localhost"),  # Composes custom HOSTNAME fallback
    HOST_PUBLIC=(str, ""),  # Composes custom HOSTNAME
    # https://docs.djangoproject.com/en/5.2/ref/settings/#use-x-forwarded-host
    TRUST_X_FORWARDED_HOST=(bool, False),  # Composes USE_X_FORWARDED_HOST
    # --- Database & Cache ---
    # https://django-environ.readthedocs.io/en/latest/types.html#environ-env-db-url
    DATABASE_URL=(str, "postgis:///city-infrastructure-platform"),
    DATABASE_PASSWORD=(str, ""),  # Composes Django DATABASES["default"]["PASSWORD"]
    # https://django-environ.readthedocs.io/en/latest/types.html#environ-env-cache-url
    CACHE_URL=(str, "locmemcache://"),
    # --- Email Configuration ---
    # https://docs.djangoproject.com/en/5.2/ref/settings/#default-from-email
    DEFAULT_FROM_EMAIL=(str, "cityinfra@hel.fi"),
    EMAIL_URL=(str, "consolemail://"),  # Deprecated / unused
    EMAIL_HOST=(str, "localhost"),  # https://docs.djangoproject.com/en/5.2/ref/settings/#email-host
    EMAIL_HOST_USER=(str, ""),  # https://docs.djangoproject.com/en/5.2/ref/settings/#email-host-user
    EMAIL_HOST_PASSWORD=(str, ""),  # https://docs.djangoproject.com/en/5.2/ref/settings/#email-host-password
    EMAIL_PORT=(int, 587),  # https://docs.djangoproject.com/en/5.2/ref/settings/#email-port
    EMAIL_USE_TLS=(bool, True),  # https://docs.djangoproject.com/en/5.2/ref/settings/#email-use-tls
    # --- Security & Cookies ---
    # https://docs.djangoproject.com/en/5.2/ref/settings/#sessions
    CSRF_COOKIE_HTTPONLY=(bool, True),  # https://docs.djangoproject.com/en/5.2/ref/settings/#csrf-cookie-httponly
    CSRF_COOKIE_SAMESITE=(str, "Strict"),  # https://docs.djangoproject.com/en/5.2/ref/settings/#csrf-cookie-samesite
    CSRF_COOKIE_SECURE=(bool, True),  # https://docs.djangoproject.com/en/5.2/ref/settings/#csrf-cookie-secure
    SESSION_COOKIE_SAMESITE=(str, "Lax"),  # https://docs.djangoproject.com/en/5.2/ref/settings/#session-cookie-samesite
    SESSION_COOKIE_SECURE=(bool, True),  # https://docs.djangoproject.com/en/5.2/ref/settings/#session-cookie-secure
    # --- Authentication, OIDC & Tunnistamo ---
    # https://github.com/City-of-Helsinki/django-helusers
    # https://github.com/ByteInternet/drf-oidc-auth
    HELUSERS_ADGROUPS_CLAIM=(str, "groups"),
    OIDC_API_TOKEN_AUTH_AUDIENCE=(str, None),  # Composes OIDC_API_TOKEN_AUTH["AUDIENCE"]
    OIDC_API_TOKEN_AUTH_ISSUER=(str, None),  # Composes OIDC_API_TOKEN_AUTH["ISSUER"]
    OIDC_AUTHENTICATION_ENABLED=(bool, True),  # Used to toggle authentication logic checks
    OIDC_ENDPOINT=(str, None),  # Composes SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT
    SOCIAL_AUTH_TUNNISTAMO_KEY=(str, None),
    SOCIAL_AUTH_TUNNISTAMO_SECRET=(str, None),
    # Composes REST_FRAMEWORK["OIDC_LEEWAY"] (https://www.django-rest-framework.org/api-guide/settings/)
    TOKEN_AUTH_MAX_TOKEN_AGE=(int, 600),
    # --- Static Media & Cloud Storage (Azure) ---
    # Composes django-storages account_name (https://django-storages.readthedocs.io/en/latest/backends/azure.html)
    AZURE_ACCOUNT_NAME=(str, False),
    AZURE_PUBLIC_CONTAINER=(str, False),
    AZURE_PRIVATE_CONTAINER=(str, False),
    EMULATE_AZURE_BLOBSTORAGE=(bool, False),  # Overrides azure storage backend with local emulation for development
    OPENSHIFT_DEPLOYMENT=(bool, False),  # Enables azure storage backend for deployment
    STATIC_URL=(str, "/static/"),  # https://docs.djangoproject.com/en/5.2/ref/settings/#static-url
    MEDIA_URL=(str, "/media/"),  # https://docs.djangoproject.com/en/5.2/ref/settings/#media-url
    # --- Sentry & Logging ---
    # https://docs.sentry.io/platforms/python/integrations/django/#configure
    LOGGING_AUTH_DEBUG=(bool, False),  # Composes Django LOGGING["loggers"]["helusers"]["level"]
    SENTRY_DEBUG=(bool, False),  # Enables debug view that fires sentry error
    SENTRY_DSN=(str, ""),  # Composes sentry-sdk DSN (https://docs.sentry.io/platforms/python/integrations/django/)
    # --- External APIs & App Settings ---
    ADDRESS_SEARCH_BASE_URL=(str, "https://api.hel.fi/servicemap/v2/search"),
    BASEMAP_SOURCE_URL=(str, "https://kartta.hel.fi/ws/geoserver/avoindata/gwc/service/wmts"),
    CITYINFRA_MAXIMUM_RESULTS_PER_PAGE=(int, 10000),
    # --- Maintenance Mode ---
    # https://github.com/City-of-Helsinki/city-infrastructure-platform/tree/master/maintenance_mode
    MAINTENANCE_MODE_ADMIN_PATHS=(list, ["admin/jsi18n"]),
    MAINTENANCE_MODE_AUTH_PREFIXES=(list, ["ha", "auth"]),
    MAINTENANCE_MODE_HEALTH_CHECKS=(list, ["healthz", "readiness"]),
    MAINTENANCE_MODE_LANGUAGES=(list, ["fi", "sv", "en"]),
    # django-helusers environment banner
    HELUSERS_ENVIRONMENT=(str, ""),
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

# Email configuration
# Use explicit EMAIL_* variables for production SMTP
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

# Determine which email backend to use based on environment
TESTING = "test" in sys.argv or "pytest" in sys.argv[0] if sys.argv else False

if TESTING:
    # Use locmem backend for tests (emails stored in django.core.mail.outbox)
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
elif DEBUG:
    # Use console backend for development (emails printed to console)
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    # Use SMTP backend for production
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Base URL for the application (used in emails, management commands, etc.)
BASE_URL = env("BASE_URL")


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
    "admin_confirm",
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
    "django_advanced_password_validation",
    "axes",
    "guardian",
    "rangefilter",
]
LOCAL_APPS = [
    "users.apps.UsersConfig",
    "traffic_control.apps.TrafficControlConfig",
    "city_furniture.apps.CityFurnitureConfig",
    "map.apps.MapConfig",
    "city_infra_instructions.apps.CityInfraInstructionsConfig",
    "maintenance_mode.apps.MaintenanceModeConfig",
    "site_alert.apps.SiteAlertConfig",
    "admin_helper.apps.AdminHelperConfig",
]
INSTALLED_APPS = LOCAL_APPS + DJANGO_APPS + THIRD_PARTY_APPS

MIGRATION_MODULES["admin_helper"] = None  # Explicitly tell django that this app needs no migrations

AUTHENTICATION_BACKENDS = (
    "axes.backends.AxesBackend",
    "helusers.tunnistamo_oidc.TunnistamoOIDCAuth",
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)

AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/admin/login/"
SOCIAL_AUTH_TUNNISTAMO_AUTH_EXTRA_ARGUMENTS = {"ui_locales": "fi"}
WAGTAIL_SITE_NAME = _("City Infrastructure Platform")

# Maintenance Mode Whitelist Configuration
# These paths remain accessible during maintenance mode to ensure:
# - Kubernetes health/readiness probes don't fail (preventing pod restarts)
# - OIDC authentication flow completes (admin users can log in via helusers/Tunnistamo)
# - Django admin i18n catalog loads (login page translations work)
# - Language prefix detection works consistently
# Can be customized per environment via ConfigMap (see maintenance_mode/README.md)
MAINTENANCE_MODE_WHITELIST = {
    "health_checks": env.list("MAINTENANCE_MODE_HEALTH_CHECKS"),
    "auth_prefixes": env.list("MAINTENANCE_MODE_AUTH_PREFIXES"),
    "admin_paths": env.list("MAINTENANCE_MODE_ADMIN_PATHS"),
    "supported_languages": env.list("MAINTENANCE_MODE_LANGUAGES"),
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "maintenance_mode.middleware.MaintenanceModeMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "drf_custom_auth.middleware.DRFCustomAuthMiddleware",
    "axes.middleware.AxesMiddleware",
]

# Exclude the IP address from audit logging
AUDITLOG_DISABLE_REMOTE_ADDR = False

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
                "django.template.context_processors.i18n",
                "cityinfra.context_processors.git_version",
                "site_alert.context_processors.site_alerts",
            ]
        },
    }
]

WSGI_APPLICATION = "cityinfra.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

if env("DATABASE_PASSWORD"):
    DATABASES["default"]["PASSWORD"] = env("DATABASE_PASSWORD")

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Forms - Transitional setting for Django 6.0 URLField default scheme change
# This will be removed when upgrading to Django 6.0
FORMS_URLFIELD_ASSUME_HTTPS = True


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {
        "NAME": "django_advanced_password_validation.advanced_password_validation.ContainsDigitsValidator",
        "OPTIONS": {"min_digits": 1},
    },
    {
        "NAME": "django_advanced_password_validation.advanced_password_validation.ContainsUppercaseValidator",
        "OPTIONS": {"min_uppercase": 1},
    },
    {
        "NAME": "django_advanced_password_validation.advanced_password_validation.ContainsLowercaseValidator",
        "OPTIONS": {"min_lowercase": 1},
    },
    {
        "NAME": "django_advanced_password_validation.advanced_password_validation.ContainsSpecialCharactersValidator",
        "OPTIONS": {"min_characters": 1},
    },
]

# Cookie security settings
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE")
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE")
CSRF_COOKIE_HTTPONLY = env.bool("CSRF_COOKIE_HTTPONLY")
CSRF_COOKIE_SAMESITE = env.str("CSRF_COOKIE_SAMESITE")
SESSION_COOKIE_SAMESITE = env.str("SESSION_COOKIE_SAMESITE")

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = "fi"
LANGUAGES = [("fi", _("Finnish")), ("en", _("English")), ("sv", _("Swedish"))]
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
    "icons": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "allow_overwrite": True,
        },
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
}
STATICFILES_DIRS = [checkout_dir("map-view/build/static")]

# Whether to trust X-Forwarded-Host headers for all purposes
# where Django would need to make use of its own hostname
# fe. generating absolute URLs pointing to itself
# Most often used in reverse proxy setups
USE_X_FORWARDED_HOST = env("TRUST_X_FORWARDED_HOST")

CITYINFRA_MAXIMUM_RESULTS_PER_PAGE = env("CITYINFRA_MAXIMUM_RESULTS_PER_PAGE")

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "helusers.oidc.ApiTokenAuthentication",
        "drf_custom_auth.authentication.LastApiUseTokenAuthentication",
        "drf_custom_auth.authentication.LastApiUseBasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "cityinfra.drf_utils.MaxLimitOffsetPagination",
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

if not DEBUG:
    SPECTACULAR_SETTINGS.update({"SWAGGER_UI_SETTINGS": {"url": "/static/traffic_control/openapi/openapi.yaml"}})

# django-cors
if DEBUG:
    CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOWED_ORIGIN_REGEXES = env("CORS_ALLOWED_ORIGIN_REGEXES")

# Azurite-specific configuration, meant only for local testing
EMULATE_AZURE_BLOBSTORAGE = env.bool("EMULATE_AZURE_BLOBSTORAGE")
if EMULATE_AZURE_BLOBSTORAGE:
    print("Using azurite (azure emulator)")
    STORAGES["default"] = {
        "BACKEND": "cityinfra.storages.backends.non_leaky_azure_storage.NonLeakyAzureStorage",
        "OPTIONS": {
            "azure_container": "uploads",
            # NOTE (2025-10-08 thiago): This is public info
            # https://github.com/Azure/Azurite/blob/92743bac3cf580c6dfe1ecc9ac777a6ce16cd985/README.md#connection-strings
            "connection_string": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
            # NOTE (2025-10-15 thiago)
            # I'd prefer to ensure predictable and overwritable paths to produce fewer orphaned files in the storage,
            # but the current deployments of the platform do the default django behavior of adding a randomized suffix
            # to the filename, so explicitly prevent overwrite for now.
            #
            # It's important to notice that allowing overwrites would also require a rearrangement on how files are
            # stored. Currently, they go to CLOUD/STORAGE_ACCOUNT/STORAGE/some-model/file.name (see the model code). If
            # one wants to allow overwrites within an object, they'd have to go to a different path, for example
            # CLOUD/STORAGE_ACCOUNT/STORAGE/some-model/:row-pk/file.name
            #
            # So a lot of administrative tasks to do such a move
            "overwrite_files": False,  # Don't touch before reading dissertation above
        },
    }

    STORAGES["icons"] = {
        "BACKEND": "cityinfra.storages.backends.non_leaky_azure_storage.NonLeakyAzureStorage",
        "OPTIONS": {
            "azure_container": "media",
            # NOTE (2025-09-11 thiago): This is public info
            # https://github.com/Azure/Azurite/blob/92743bac3cf580c6dfe1ecc9ac777a6ce16cd985/README.md#connection-strings
            "connection_string": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
            "overwrite_files": True,
        },
    }

# OpenShift-specific configuration
OPENSHIFT_DEPLOYMENT = env.bool("OPENSHIFT_DEPLOYMENT")
if OPENSHIFT_DEPLOYMENT:
    # Use Azure Storage Container as file storage in OpenShift deployment
    STORAGES["default"] = {
        "BACKEND": "cityinfra.storages.backends.non_leaky_azure_storage.NonLeakyAzureStorage",
        "OPTIONS": {
            "account_name": env.str("AZURE_ACCOUNT_NAME"),
            "azure_container": env.str("AZURE_PRIVATE_CONTAINER"),
            "sas_token": env.str("AZURE_PRIVATE_SAS_TOKEN"),
        },
    }

    # Icons storage
    STORAGES["icons"] = {
        "BACKEND": "cityinfra.storages.backends.non_leaky_azure_storage.NonLeakyAzureStorage",
        "OPTIONS": {
            "account_name": env.str("AZURE_ACCOUNT_NAME"),
            "azure_container": env.str("AZURE_PUBLIC_CONTAINER"),
            "sas_token": env.str("AZURE_PUBLIC_SAS_TOKEN"),
            "overwrite_files": True,
        },
    }

if EMULATE_AZURE_BLOBSTORAGE and OPENSHIFT_DEPLOYMENT:
    raise ImproperlyConfigured(
        "You cannot have EMULATE_AZURE_BLOBSTORAGE and OPENSHIFT_DEPLOYMENT enabled at the same time"
    )

# Sentry-SDK
SENTRY_DSN = env.str("SENTRY_DSN")
SENTRY_DEBUG = env.bool("SENTRY_DEBUG")
VERSION = env.str("VERSION")
if SENTRY_DSN:
    sentry_sdk.init(dsn=SENTRY_DSN, integrations=[DjangoIntegration()], release=VERSION)

# Custom settings
SRID = 3879  # the spatial reference id used for geometries

# Format for invidual SRID boundary box is:
# x0,y0, x1, y1
# for 3879 this is actually subset of it, bounding box is for Helsinki area only
# the whole 3879 would be {3879: (21532262.0, 3639452.31, 26927342.37, 9557869.6)}
SRID_BOUNDARIES = {3879: (25487917.144, 6645439.071, 25514074.175, 6687278.623)}

BASEMAP_SOURCE_URL = env.str("BASEMAP_SOURCE_URL")
ADDRESS_SEARCH_BASE_URL = env.str("ADDRESS_SEARCH_BASE_URL")

# Import / Export
IMPORT_EXPORT_USE_TRANSACTIONS = True
# Require view permission even to export template
IMPORT_EXPORT_EXPORT_PERMISSION_CODE = "view"

# WFS
GISSERVER_USE_DB_RENDERING = False

# Virus scan
CLAMAV_BASE_URL = env.str("CLAMAV_BASE_URL", "http://localhost:3030")

# django-helusers environment banner
HELUSERS_ENVIRONMENT = env.str("HELUSERS_ENVIRONMENT", "")
# fileupload types
ALLOWED_FILE_UPLOAD_TYPES = [
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".pdf",
    ".txt",
    ".png",
    ".jpg",
    ".bmp",
    ".tif",
    ".svg",
    ".dwg",
    ".dgn",
    ".csv",
]

# PNG icons
PNG_ICON_SIZES = [32, 64, 128, 256]
CITY_FURNITURE_DEVICE_TYPE_ICON_BASE_PATH = "icons/city_furniture_device_type/"
CITY_FURNITURE_DEVICE_TYPE_SVG_ICON_DESTINATION = f"{CITY_FURNITURE_DEVICE_TYPE_ICON_BASE_PATH}svg/"
CITY_FURNITURE_DEVICE_TYPE_PNG_ICON_DESTINATION = f"{CITY_FURNITURE_DEVICE_TYPE_ICON_BASE_PATH}png/"
TRAFFIC_CONTROL_DEVICE_TYPE_ICON_BASE_PATH = "icons/traffic_control_device_type/"
TRAFFIC_CONTROL_DEVICE_TYPE_SVG_ICON_DESTINATION = f"{TRAFFIC_CONTROL_DEVICE_TYPE_ICON_BASE_PATH}svg/"
TRAFFIC_CONTROL_DEVICE_TYPE_PNG_ICON_DESTINATION = f"{TRAFFIC_CONTROL_DEVICE_TYPE_ICON_BASE_PATH}png/"

# django-axes settings for login failure limitation
AXES_FAILURE_LIMIT = 6
AXES_COOLOFF_TIME = 0.5
AXES_RESET_ON_SUCCESS = True
AXES_CLIENT_IP_CALLABLE = "traffic_control.utils.get_client_ip"

DEBUG_TOOLBAR = False
if DEBUG:
    # Setup debug toolbar
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

    # Setup detection of n+1 problems on console
    INSTALLED_APPS.append("zeal")
    MIDDLEWARE.append("zeal.middleware.zeal_middleware")
    ZEAL_RAISE = False
