from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.template import loader
from django.utils.translation import activate


class MaintenanceModeMiddleware:
    """
    Middleware that blocks all requests when maintenance mode is active.

    Returns 503 Service Unavailable with a maintenance page for blocked requests.

    Whitelisted paths (configured via MAINTENANCE_MODE_WHITELIST setting):
    - Health check endpoints (healthz, readiness) - prevents Kubernetes pod restarts
    - Authentication URLs (ha/, auth/) - enables OIDC login/logout via helusers/Tunnistamo
    - Admin JavaScript i18n (admin/jsi18n) - supports login page translations
    - Admin login pages - allows superusers to access admin during maintenance

    Environment variables (override defaults via ConfigMap):
    - MAINTENANCE_MODE_HEALTH_CHECKS: Health/readiness probe endpoints
    - MAINTENANCE_MODE_AUTH_PREFIXES: Authentication URL prefixes (includes login and logout)
    - MAINTENANCE_MODE_ADMIN_PATHS: Admin-related paths
    - MAINTENANCE_MODE_LANGUAGES: Supported language codes

    Access rules:
    - Whitelisted paths: accessible to all users (including logout URLs)
    - Admin login page: accessible to unauthenticated users
    - Admin pages: accessible only to authenticated superusers
    - All other pages: blocked with 503
    """

    def __init__(self, get_response=None):
        self.get_response = get_response
        self._maintenance_mode = None
        self._last_check = None

    def _is_maintenance_active(self):
        """Check if maintenance mode is active. Cache for performance."""
        import time

        from maintenance_mode.models import MaintenanceMode

        current_time = time.time()

        # Cache for 10 seconds to avoid hitting the database on every request
        if self._last_check is None or (current_time - self._last_check) > 10:
            try:
                maintenance = MaintenanceMode.get_instance()
                self._maintenance_mode = maintenance
                self._last_check = current_time
            except Exception:
                # If there's any error accessing the database, don't block requests
                self._maintenance_mode = None
                self._last_check = current_time

        return self._maintenance_mode and self._maintenance_mode.is_active

    def _get_maintenance_message(self, request: HttpRequest) -> str:
        """
        Get the maintenance message in the current language.

        Detects language from URL path (e.g., /fi/... or /en/...) since this middleware
        runs before LocaleMiddleware sets the language.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            str: The maintenance message in the detected language.
        """
        if not self._maintenance_mode:
            return "System is under maintenance. Please try again later."

        # Try to get language from URL path first (e.g., /fi/admin/, /en/api/)
        path_parts = request.path.strip("/").split("/")
        language = None
        if len(path_parts) > 0 and len(path_parts[0]) == 2:
            # Check if first part looks like a language code (2 characters)
            potential_lang = path_parts[0].lower()
            if potential_lang in settings.MAINTENANCE_MODE_WHITELIST["supported_languages"]:
                language = potential_lang

        # Fallback to Django's default language from settings
        if not language:
            language = settings.LANGUAGE_CODE

        # Map language to appropriate message
        messages = {
            "fi": self._maintenance_mode.message_fi or "Järjestelmä on huoltotilassa. Yritä myöhemmin uudelleen.",
            "sv": self._maintenance_mode.message_sv or "Systemet är under underhåll. Försök igen senare.",
        }
        return messages.get(
            language, self._maintenance_mode.message_en or "System is under maintenance. Please try again later."
        )

    def _is_admin_login_page(self, path_parts, admin_index):
        """Check if the path is an admin login page or root admin path."""
        return (
            len(path_parts) > admin_index
            and path_parts[admin_index] == "admin"
            and (
                len(path_parts) == admin_index + 1  # /admin/ or /en/admin/
                or (len(path_parts) > admin_index + 1 and path_parts[admin_index + 1] == "login")
            )  # /admin/login/ or /en/admin/login/
        )

    def _should_allow_request(self, request: HttpRequest, path_parts: list[str]) -> bool:
        """
        Determine if request should be allowed during maintenance mode.

        Args:
            request (HttpRequest): The incoming HTTP request.
            path_parts (list[str]): URL path split into parts.

        Returns:
            bool: True if request should be allowed, False if it should be blocked with 503.
        """
        path_stripped = request.path.strip("/")

        # Allow health check endpoints (configured via MAINTENANCE_MODE_HEALTH_CHECKS)
        if path_stripped in settings.MAINTENANCE_MODE_WHITELIST["health_checks"]:
            return True

        # Allow authentication URLs for OIDC/OAuth login and logout flows
        # This includes login, logout, OAuth callbacks, and disconnect endpoints
        # Accessible to ALL users (authenticated and unauthenticated) during maintenance
        # Supports both direct paths (/ha/, /auth/) and language-prefixed (/fi/ha/, /en/auth/)
        if len(path_parts) > 0:
            first_part = path_parts[0]
            auth_prefixes = settings.MAINTENANCE_MODE_WHITELIST["auth_prefixes"]
            supported_languages = settings.MAINTENANCE_MODE_WHITELIST["supported_languages"]

            # Check if first part is auth prefix or language code followed by auth prefix
            if first_part in auth_prefixes:
                return True
            if len(path_parts) > 1 and first_part in supported_languages and path_parts[1] in auth_prefixes:
                return True

        # Allow admin JavaScript i18n catalog for login page translations
        if any(admin_path in request.path for admin_path in settings.MAINTENANCE_MODE_WHITELIST["admin_paths"]):
            return True

        # Check if 'admin' is in the first two parts of the path
        is_admin_path = len(path_parts) > 0 and (
            path_parts[0] == "admin" or (len(path_parts) > 1 and path_parts[1] == "admin")
        )

        # Non-admin paths are blocked
        if not is_admin_path:
            return False

        # For admin paths: allow superusers or unauthenticated users on login page
        admin_index = 0 if path_parts[0] == "admin" else 1
        is_superuser = request.user.is_authenticated and request.user.is_superuser
        is_login_page_anonymous = not request.user.is_authenticated and self._is_admin_login_page(
            path_parts, admin_index
        )

        return is_superuser or is_login_page_anonymous

    def _detect_language_code(self, request: HttpRequest) -> str:
        """
        Detect language code from URL path or settings.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            str: The detected language code (e.g., 'fi', 'en', 'sv').
        """
        path_parts = request.path.strip("/").split("/")
        if len(path_parts) > 0 and len(path_parts[0]) == 2:
            potential_lang = path_parts[0].lower()
            if potential_lang in settings.MAINTENANCE_MODE_WHITELIST["supported_languages"]:
                return potential_lang
        return settings.LANGUAGE_CODE

    def __call__(self, request):
        # Check if maintenance mode is active
        if not self._is_maintenance_active():
            return self.get_response(request)

        # Check if request should be allowed
        path_parts = request.path.strip("/").split("/")
        if self._should_allow_request(request, path_parts):
            return self.get_response(request)

        # Block all other requests with 503
        language_code = self._detect_language_code(request)
        activate(language_code)

        template = loader.get_template("maintenance_mode/maintenance.html")
        context = {
            "message": self._get_maintenance_message(request),
            "language_code": language_code,
        }
        html = template.render(context, request)
        return HttpResponse(html, status=503)
