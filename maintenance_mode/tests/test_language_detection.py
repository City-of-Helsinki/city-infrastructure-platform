import pytest

from maintenance_mode.models import MaintenanceMode


@pytest.fixture
def maintenance_mode_active(db):
    """Get maintenance mode instance and set to active with custom messages"""
    maintenance = MaintenanceMode.get_instance()
    maintenance.is_active = True
    maintenance.message_fi = "Huoltoviesti suomeksi"
    maintenance.message_en = "Maintenance message in English"
    maintenance.message_sv = "Underhållsmeddelande på svenska"
    maintenance.save()
    return maintenance


@pytest.mark.django_db
class TestLanguageDetection:
    """Test that maintenance message language is correctly detected from URL path"""

    def test_finnish_message_from_path(self, client, maintenance_mode_active):
        """Test that Finnish message is shown for /fi/ paths"""
        response = client.get("/fi/api/")
        assert response.status_code == 503
        assert "Huoltoviesti suomeksi" in response.content.decode()

    def test_english_message_from_path(self, client, maintenance_mode_active):
        """Test that English message is shown for /en/ paths"""
        response = client.get("/en/api/")
        assert response.status_code == 503
        assert "Maintenance message in English" in response.content.decode()

    def test_swedish_message_from_path(self, client, maintenance_mode_active):
        """Test that Swedish message is shown for /sv/ paths"""
        response = client.get("/sv/api/")
        assert response.status_code == 503
        assert "Underhållsmeddelande på svenska" in response.content.decode()

    def test_default_finnish_message_without_language_prefix(self, client, maintenance_mode_active):
        """Test that Finnish language is used for paths without language prefix (default language)"""
        response = client.get("/api/")
        assert response.status_code == 503
        content = response.content.decode()
        # Should use Finnish language code when no language in path
        assert 'lang="fi"' in content
        # Should show the Finnish custom message
        assert "Huoltoviesti suomeksi" in content

    def test_language_detection_works_on_homepage(self, client, maintenance_mode_active):
        """Test language detection works on root paths"""
        # Finnish homepage
        response_fi = client.get("/fi/")
        assert response_fi.status_code == 503
        assert "Huoltoviesti suomeksi" in response_fi.content.decode()

        # English homepage
        response_en = client.get("/en/")
        assert response_en.status_code == 503
        assert "Maintenance message in English" in response_en.content.decode()

        # Swedish homepage
        response_sv = client.get("/sv/")
        assert response_sv.status_code == 503
        assert "Underhållsmeddelande på svenska" in response_sv.content.decode()
