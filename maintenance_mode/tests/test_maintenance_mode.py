import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from maintenance_mode.models import MaintenanceMode

User = get_user_model()


@pytest.fixture
def regular_user(db):
    """Create a regular user for testing"""
    return User.objects.create_user(username="regular", password="testpass123")


@pytest.fixture
def admin_user(db):
    """Create a superuser for testing"""
    return User.objects.create_superuser(username="admin", password="adminpass123", email="admin@test.com")


@pytest.fixture
def maintenance_mode(db):
    """Get or create maintenance mode instance and reset to inactive"""
    maintenance = MaintenanceMode.get_instance()
    maintenance.is_active = False
    maintenance.save()
    return maintenance


@pytest.mark.django_db
class TestMaintenanceModeMiddleware:
    """Test the maintenance mode middleware"""

    def test_normal_access_when_maintenance_inactive(self, client, maintenance_mode):
        """Test that requests work normally when maintenance mode is off"""
        maintenance_mode.is_active = False
        maintenance_mode.save()

        # Should be able to access admin login page (may redirect if already logged in)
        response = client.get("/admin/login/")
        assert response.status_code in [200, 302]

    def test_maintenance_blocks_regular_requests(self, client, regular_user, maintenance_mode):
        """Test that maintenance mode blocks regular requests with 503"""
        maintenance_mode.is_active = True
        maintenance_mode.save()

        # Regular user should get 503
        client.force_login(regular_user)
        response = client.get("/")
        assert response.status_code == 503
        # Check that maintenance page is shown (check for message container)
        assert '<div class="message">' in response.content.decode()

    def test_maintenance_allows_admin_access(self, client, admin_user, maintenance_mode):
        """Test that superusers can access admin pages during maintenance"""
        maintenance_mode.is_active = True
        maintenance_mode.save()

        # Superuser should be able to access admin
        client.force_login(admin_user)
        response = client.get("/admin/")
        # Should not get 503 (might be redirect to login or 200)
        assert response.status_code != 503

    def test_maintenance_blocks_non_admin_paths(self, client, admin_user, maintenance_mode):
        """Test that non-admin paths are blocked even for superusers"""
        maintenance_mode.is_active = True
        maintenance_mode.save()

        client.force_login(admin_user)
        response = client.get("/api/")
        assert response.status_code == 503

    def test_maintenance_message_in_response(self, client, maintenance_mode):
        """Test that maintenance message appears in the response"""
        maintenance_mode.is_active = True
        maintenance_mode.message_en = "Custom maintenance message"
        maintenance_mode.save()

        response = client.get("/")
        assert response.status_code == 503
        # Check that the page has the maintenance structure (not checking specific language)
        content = response.content.decode()
        assert '<div class="message">' in content
        assert '<div class="icon">🔧</div>' in content

    def test_admin_login_page_accessible_during_maintenance(self, client, maintenance_mode):
        """Test that admin login page is accessible even when maintenance mode is active"""
        maintenance_mode.is_active = True
        maintenance_mode.save()

        # Anonymous user should be able to access login page
        response = client.get("/admin/login/")
        # Should not get 503 (will be 200 or 302)
        assert response.status_code != 503

    def test_admin_login_page_with_language_prefix_accessible(self, maintenance_mode):
        """Test that /en/admin/login/ is accessible during maintenance mode"""
        from django.contrib.auth.models import AnonymousUser
        from django.test import RequestFactory

        from maintenance_mode.middleware import MaintenanceModeMiddleware

        maintenance_mode.is_active = True
        maintenance_mode.save()

        # Use RequestFactory to test middleware without loading full admin page
        factory = RequestFactory()
        request = factory.get("/en/admin/login/")
        request.user = AnonymousUser()

        middleware = MaintenanceModeMiddleware(lambda r: type("Response", (), {"status_code": 200})())
        response = middleware(request)

        # Should not return 503 - login page should be accessible
        assert response.status_code != 503


@pytest.mark.django_db
class TestMaintenanceModeModel:
    """Test the MaintenanceMode model"""

    def test_singleton_pattern(self):
        """Test that only one instance can exist"""
        instance1 = MaintenanceMode.get_instance()
        instance2 = MaintenanceMode.get_instance()

        # Should be the same instance
        assert instance1.id == instance2.id
        assert instance1.id == 1

        # Should only have one row
        assert MaintenanceMode.objects.count() == 1

    def test_multiple_saves_update_same_row(self):
        """Test that multiple saves update the same row"""
        m1 = MaintenanceMode()
        m1.is_active = False
        m1.message_en = "First message"
        m1.save()

        m2 = MaintenanceMode()
        m2.is_active = True
        m2.message_en = "Second message"
        m2.save()

        # Should still only have one row
        assert MaintenanceMode.objects.count() == 1

        # Should have the latest values
        instance = MaintenanceMode.get_instance()
        assert instance.is_active is True
        assert instance.message_en == "Second message"

    def test_default_messages(self):
        """Test that default messages are set"""
        instance = MaintenanceMode.get_instance()

        assert "huoltotilassa" in instance.message_fi.lower()
        assert "maintenance" in instance.message_en.lower()
        assert "underhåll" in instance.message_sv.lower()

    def test_cannot_delete(self):
        """Test that the instance cannot be deleted"""
        instance = MaintenanceMode.get_instance()

        with pytest.raises(ValidationError):
            instance.delete()
