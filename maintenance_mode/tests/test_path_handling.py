import pytest
from django.test import RequestFactory

from maintenance_mode.middleware import MaintenanceModeMiddleware
from maintenance_mode.models import MaintenanceMode


@pytest.fixture
def admin_user(db):
    """Create a superuser for testing"""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_superuser(username="admin", password="adminpass123", email="admin@test.com")


@pytest.fixture
def staff_user(db):
    """Create a staff user (not superuser) for testing"""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(
        username="staff",
        password="staffpass123",
        is_staff=True,  # Staff but NOT superuser
        is_superuser=False,
    )


@pytest.fixture
def maintenance_mode_active(db):
    """Get maintenance mode instance and set to active"""
    maintenance = MaintenanceMode.get_instance()
    maintenance.is_active = True
    maintenance.save()
    return maintenance


@pytest.mark.django_db
class TestMaintenanceModePathHandling:
    """Test that middleware correctly handles paths with and without language codes"""

    def test_admin_path_without_language_code(self, admin_user, maintenance_mode_active):
        """Test /admin/ path is allowed for superusers"""
        factory = RequestFactory()
        request = factory.get("/admin/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503
        assert response.status_code != 503

    def test_admin_path_with_en_language_code(self, admin_user, maintenance_mode_active):
        """Test /en/admin/ path is allowed for superusers"""
        factory = RequestFactory()
        request = factory.get("/en/admin/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503
        assert response.status_code != 503

    def test_admin_path_with_fi_language_code(self, admin_user, maintenance_mode_active):
        """Test /fi/admin/ path is allowed for superusers"""
        factory = RequestFactory()
        request = factory.get("/fi/admin/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503
        assert response.status_code != 503

    def test_admin_path_with_sv_language_code(self, admin_user, maintenance_mode_active):
        """Test /sv/admin/ path is allowed for superusers"""
        factory = RequestFactory()
        request = factory.get("/sv/admin/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503
        assert response.status_code != 503

    def test_admin_subpath_without_language_code(self, admin_user, maintenance_mode_active):
        """Test /admin/login/ path is allowed for superusers"""
        factory = RequestFactory()
        request = factory.get("/admin/login/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503
        assert response.status_code != 503

    def test_admin_subpath_with_language_code(self, admin_user, maintenance_mode_active):
        """Test /en/admin/login/ path is allowed for superusers"""
        factory = RequestFactory()
        request = factory.get("/en/admin/login/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503
        assert response.status_code != 503

    def test_non_admin_path_blocked(self, admin_user, maintenance_mode_active):
        """Test non-admin paths are blocked even for superusers"""
        factory = RequestFactory()
        request = factory.get("/v1/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should return 503
        assert response.status_code == 503

    def test_admin_login_page_accessible_to_everyone(self, maintenance_mode_active):
        """Test that admin login page is accessible to everyone during maintenance"""
        from django.contrib.auth.models import AnonymousUser

        factory = RequestFactory()
        request = factory.get("/admin/login/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503 - login page must be accessible
        assert response.status_code != 503

    def test_admin_login_page_with_language_prefix_accessible(self, maintenance_mode_active):
        """Test that /en/admin/login/ is accessible to everyone during maintenance"""
        from django.contrib.auth.models import AnonymousUser

        factory = RequestFactory()
        request = factory.get("/en/admin/login/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503 - login page must be accessible
        assert response.status_code != 503

    def test_root_admin_path_accessible_to_everyone(self, maintenance_mode_active):
        """Test that /admin/ (root) is accessible to everyone (redirects to login)"""
        from django.contrib.auth.models import AnonymousUser

        factory = RequestFactory()
        request = factory.get("/admin/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503 - root admin path redirects to login
        assert response.status_code != 503

    def test_root_admin_path_with_language_prefix_accessible(self, maintenance_mode_active):
        """Test that /fi/admin/ (root with language) is accessible to everyone"""
        from django.contrib.auth.models import AnonymousUser

        factory = RequestFactory()
        request = factory.get("/fi/admin/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503 - root admin path redirects to login
        assert response.status_code != 503

    def test_staff_user_blocked_from_admin_pages(self, staff_user, maintenance_mode_active):
        """Test that authenticated staff users (non-superusers) are blocked from admin pages"""
        factory = RequestFactory()
        request = factory.get("/admin/")
        request.user = staff_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should return 503 - staff users are not allowed during maintenance
        assert response.status_code == 503

    def test_staff_user_blocked_from_admin_subpages(self, staff_user, maintenance_mode_active):
        """Test that staff users are blocked from admin subpages"""
        factory = RequestFactory()
        request = factory.get("/admin/users/")
        request.user = staff_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should return 503 - staff users are not allowed during maintenance
        assert response.status_code == 503

    def test_staff_user_blocked_with_language_prefix(self, staff_user, maintenance_mode_active):
        """Test that staff users are blocked from admin pages with language prefix"""
        factory = RequestFactory()
        request = factory.get("/en/admin/")
        request.user = staff_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should return 503 - staff users are not allowed during maintenance
        assert response.status_code == 503

    def test_healthz_accessible_during_maintenance(self, maintenance_mode_active):
        """Test that /healthz health-check endpoint is always accessible during maintenance"""
        from django.contrib.auth.models import AnonymousUser

        factory = RequestFactory()
        request = factory.get("/healthz")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503 - health check must always work
        assert response.status_code != 503

    def test_healthz_with_trailing_slash_accessible(self, maintenance_mode_active):
        """Test that /healthz/ (with trailing slash) is accessible during maintenance"""
        from django.contrib.auth.models import AnonymousUser

        factory = RequestFactory()
        request = factory.get("/healthz/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503 - health check must always work
        assert response.status_code != 503

    def test_healthz_accessible_for_all_users(self, admin_user, staff_user, maintenance_mode_active):
        """Test that health-check is accessible regardless of user authentication state"""
        factory = RequestFactory()
        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())

        # Test with superuser
        request = factory.get("/healthz")
        request.user = admin_user
        response = middleware(request)
        assert response.status_code != 503

        # Test with staff user
        request = factory.get("/healthz")
        request.user = staff_user
        response = middleware(request)
        assert response.status_code != 503

        # Test with anonymous user
        from django.contrib.auth.models import AnonymousUser

        request = factory.get("/healthz")
        request.user = AnonymousUser()
        response = middleware(request)
        assert response.status_code != 503
