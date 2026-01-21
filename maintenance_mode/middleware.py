from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from django.utils.translation import activate


class MaintenanceModeMiddleware:
    """
    Middleware that blocks all requests when maintenance mode is active.
    Returns 503 Service Unavailable with a maintenance page.

    Exceptions:
    - Unauthenticated users can access admin login page (so superusers can log in)
    - Authenticated superusers can access all admin pages
    - Authenticated non-superusers (staff, regular users) are blocked from all pages
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

    def _get_maintenance_message(self, request):
        """Get the maintenance message in the current language.

        Detects language from URL path (e.g., /fi/... or /en/...) since this middleware
        runs before LocaleMiddleware sets the language.
        """
        if not self._maintenance_mode:
            return "System is under maintenance. Please try again later."

        # Try to get language from URL path first (e.g., /fi/admin/, /en/api/)
        path_parts = request.path.strip("/").split("/")
        language = None
        if len(path_parts) > 0 and len(path_parts[0]) == 2:
            # Check if first part looks like a language code (2 characters)
            potential_lang = path_parts[0].lower()
            if potential_lang in ["fi", "sv", "en"]:
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

    def _should_allow_request(self, request, path_parts):
        """Determine if request should be allowed during maintenance mode."""
        # Always allow health check endpoint, otherwise pods with health checks would be marked unhealthy
        # and restarted continuously.
        if request.path.strip("/") == "healthz":
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

    def _detect_language_code(self, request):
        """Detect language code from URL path or settings."""
        path_parts = request.path.strip("/").split("/")
        if len(path_parts) > 0 and len(path_parts[0]) == 2:
            potential_lang = path_parts[0].lower()
            if potential_lang in ["fi", "sv", "en"]:
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
