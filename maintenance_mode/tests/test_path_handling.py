import pytest

from maintenance_mode.middleware import MaintenanceModeMiddleware
from maintenance_mode.models import MaintenanceMode


@pytest.fixture
def staff_user(db, django_user_model):
    """Create a staff user (not superuser) for testing"""
    return django_user_model.objects.create_user(
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

    def test_admin_path_without_language_code(self, rf, admin_user, maintenance_mode_active):
        """Test /admin/ path is allowed for superusers"""
        request = rf.get("/admin/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503
        assert response.status_code != 503

    def test_admin_path_with_en_language_code(self, rf, admin_user, maintenance_mode_active):
        """Test /en/admin/ path is allowed for superusers"""
        request = rf.get("/en/admin/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503
        assert response.status_code != 503

    def test_admin_path_with_fi_language_code(self, rf, admin_user, maintenance_mode_active):
        """Test /fi/admin/ path is allowed for superusers"""
        request = rf.get("/fi/admin/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503
        assert response.status_code != 503

    def test_admin_path_with_sv_language_code(self, rf, admin_user, maintenance_mode_active):
        """Test /sv/admin/ path is allowed for superusers"""
        request = rf.get("/sv/admin/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503
        assert response.status_code != 503

    def test_admin_subpath_without_language_code(self, rf, admin_user, maintenance_mode_active):
        """Test /admin/login/ path is allowed for superusers"""
        request = rf.get("/admin/login/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503
        assert response.status_code != 503

    def test_admin_subpath_with_language_code(self, rf, admin_user, maintenance_mode_active):
        """Test /en/admin/login/ path is allowed for superusers"""

        request = rf.get("/en/admin/login/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503
        assert response.status_code != 503

    def test_non_admin_path_blocked(self, rf, admin_user, maintenance_mode_active):
        """Test non-admin paths are blocked even for superusers"""

        request = rf.get("/v1/")
        request.user = admin_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should return 503
        assert response.status_code == 503

    def test_admin_login_page_accessible_to_everyone(self, rf, maintenance_mode_active):
        """Test that admin login page is accessible to everyone during maintenance"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/admin/login/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503 - login page must be accessible
        assert response.status_code != 503

    def test_admin_login_page_with_language_prefix_accessible(self, rf, maintenance_mode_active):
        """Test that /en/admin/login/ is accessible to everyone during maintenance"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/en/admin/login/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503 - login page must be accessible
        assert response.status_code != 503

    def test_root_admin_path_accessible_to_everyone(self, rf, maintenance_mode_active):
        """Test that /admin/ (root) is accessible to everyone (redirects to login)"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/admin/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503 - root admin path redirects to login
        assert response.status_code != 503

    def test_root_admin_path_with_language_prefix_accessible(self, rf, maintenance_mode_active):
        """Test that /fi/admin/ (root with language) is accessible to everyone"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/fi/admin/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503 - root admin path redirects to login
        assert response.status_code != 503

    def test_staff_user_blocked_from_admin_pages(self, rf, staff_user, maintenance_mode_active):
        """Test that authenticated staff users (non-superusers) are blocked from admin pages"""

        request = rf.get("/admin/")
        request.user = staff_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should return 503 - staff users are not allowed during maintenance
        assert response.status_code == 503

    def test_staff_user_blocked_from_admin_subpages(self, rf, staff_user, maintenance_mode_active):
        """Test that staff users are blocked from admin subpages"""

        request = rf.get("/admin/users/")
        request.user = staff_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should return 503 - staff users are not allowed during maintenance
        assert response.status_code == 503

    def test_staff_user_blocked_with_language_prefix(self, rf, staff_user, maintenance_mode_active):
        """Test that staff users are blocked from admin pages with language prefix"""

        request = rf.get("/en/admin/")
        request.user = staff_user

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should return 503 - staff users are not allowed during maintenance
        assert response.status_code == 503

    def test_healthz_accessible_during_maintenance(self, rf, maintenance_mode_active):
        """Test that /healthz health-check endpoint is always accessible during maintenance"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/healthz")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503 - health check must always work
        assert response.status_code != 503

    def test_healthz_with_trailing_slash_accessible(self, rf, maintenance_mode_active):
        """Test that /healthz/ (with trailing slash) is accessible during maintenance"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/healthz/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503 - health check must always work
        assert response.status_code != 503

    def test_healthz_accessible_for_all_users(self, rf, admin_user, staff_user, maintenance_mode_active):
        """Test that health-check is accessible regardless of user authentication state"""

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())

        # Test with superuser
        request = rf.get("/healthz")
        request.user = admin_user
        response = middleware(request)
        assert response.status_code != 503

        # Test with staff user
        request = rf.get("/healthz")
        request.user = staff_user
        response = middleware(request)
        assert response.status_code != 503

        # Test with anonymous user
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/healthz")
        request.user = AnonymousUser()
        response = middleware(request)
        assert response.status_code != 503

    def test_readiness_endpoint_accessible_during_maintenance(self, rf, maintenance_mode_active):
        """Test that /readiness endpoint is accessible during maintenance for Kubernetes probes"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/readiness")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        assert response.status_code != 503

    def test_ha_login_accessible_during_maintenance(self, rf, maintenance_mode_active):
        """Test that /ha/login/ (helusers login) is accessible during maintenance"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/ha/login/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        assert response.status_code != 503

    def test_ha_logout_accessible_during_maintenance(self, rf, maintenance_mode_active):
        """Test that /ha/logout/ (helusers logout) is accessible during maintenance"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/ha/logout/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        assert response.status_code != 503

    def test_auth_login_tunnistamo_accessible(self, rf, maintenance_mode_active):
        """Test that /auth/login/tunnistamo/ (social-auth OIDC start) is accessible"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/auth/login/tunnistamo/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        assert response.status_code != 503

    def test_auth_complete_tunnistamo_accessible(self, rf, maintenance_mode_active):
        """Test that /auth/complete/tunnistamo/ (OAuth callback) is accessible - critical for login"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/auth/complete/tunnistamo/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        assert response.status_code != 503

    def test_auth_disconnect_tunnistamo_accessible(self, rf, maintenance_mode_active):
        """Test that /auth/disconnect/tunnistamo/ is accessible during maintenance"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/auth/disconnect/tunnistamo/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        assert response.status_code != 503

    def test_language_prefixed_ha_login_accessible(self, rf, maintenance_mode_active):
        """Test that /fi/ha/login/ (language-prefixed helusers) is accessible"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/fi/ha/login/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        assert response.status_code != 503

    def test_language_prefixed_auth_complete_accessible(self, rf, maintenance_mode_active):
        """Test that /en/auth/complete/tunnistamo/ (language-prefixed OAuth callback) is accessible"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/en/auth/complete/tunnistamo/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        assert response.status_code != 503

    def test_sv_ha_logout_accessible(self, rf, maintenance_mode_active):
        """Test that /sv/ha/logout/ (Swedish language prefix) is accessible"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/sv/ha/logout/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        assert response.status_code != 503

    def test_admin_jsi18n_accessible(self, rf, maintenance_mode_active):
        """Test that /admin/jsi18n/ (Django admin JavaScript i18n) is accessible"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/admin/jsi18n/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        assert response.status_code != 503

    def test_language_prefixed_admin_jsi18n_accessible(self, rf, maintenance_mode_active):
        """Test that /fi/admin/jsi18n/ (language-prefixed admin i18n) is accessible"""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/fi/admin/jsi18n/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        assert response.status_code != 503

    def test_auth_paths_accessible_for_all_user_types(self, rf, admin_user, staff_user, maintenance_mode_active):
        """Test that authentication paths work for all user authentication states"""

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())

        # Test /ha/login/ with different user types
        for user in [admin_user, staff_user]:
            request = rf.get("/ha/login/")
            request.user = user
            response = middleware(request)
            assert response.status_code != 503

        # Test with anonymous user
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/auth/complete/tunnistamo/")
        request.user = AnonymousUser()
        response = middleware(request)
        assert response.status_code != 503
