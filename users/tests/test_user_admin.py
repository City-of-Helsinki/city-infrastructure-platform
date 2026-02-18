import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from social_django.models import UserSocialAuth

from traffic_control.tests.factories import get_user
from users.admin import AuthenticationTypeFilter, UserAdmin
from users.models import User


@pytest.mark.django_db
class TestAuthenticationTypeFilter:
    """Tests for AuthenticationTypeFilter in user admin."""

    def test_lookups(self):
        """Test that filter provides correct lookup options."""
        filter_instance = AuthenticationTypeFilter(None, {}, User, UserAdmin)
        lookups = filter_instance.lookups(None, None)
        assert len(lookups) == 4
        lookup_values = [item[0] for item in lookups]
        assert "local" in lookup_values
        assert "oidc" in lookup_values
        assert "both" in lookup_values
        assert "none" in lookup_values

    def test_queryset_filter_local(self):
        """Test filtering for local-only users."""
        # Create users with different auth types
        user_local = get_user(username="local_user")
        user_local.set_password("SecureP@ssw0rd123")
        user_local.save()

        user_oidc = get_user(username="oidc_user")
        user_oidc.set_unusable_password()
        user_oidc.save()
        UserSocialAuth.objects.create(user=user_oidc, provider="tunnistamo", uid="oidc-uid")

        user_both = get_user(username="both_user")
        user_both.set_password("SecureP@ssw0rd456")
        user_both.save()
        UserSocialAuth.objects.create(user=user_both, provider="tunnistamo", uid="both-uid")

        # Test filter - need to create proper admin instance and request
        factory = RequestFactory()
        request = factory.get("/admin/users/user/", {"auth_type": "local"})
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        # The params dict tracks which params are used by filters
        params = request.GET.copy()
        filter_instance = AuthenticationTypeFilter(request, params, User, user_admin)
        # Only query the test users we created
        test_users = User.objects.filter(username__in=["local_user", "oidc_user", "both_user"])
        queryset = filter_instance.queryset(request, test_users)
        usernames = list(queryset.values_list("username", flat=True))

        assert "local_user" in usernames
        assert "oidc_user" not in usernames
        assert "both_user" not in usernames

    def test_queryset_filter_oidc(self):
        """Test filtering for OIDC-only users."""
        # Create users with different auth types
        user_local = get_user(username="local_user")
        user_local.set_password("SecureP@ssw0rd123")
        user_local.save()

        user_oidc = get_user(username="oidc_user")
        user_oidc.set_unusable_password()
        user_oidc.save()
        UserSocialAuth.objects.create(user=user_oidc, provider="tunnistamo", uid="oidc-uid")

        user_both = get_user(username="both_user")
        user_both.set_password("SecureP@ssw0rd456")
        user_both.save()
        UserSocialAuth.objects.create(user=user_both, provider="tunnistamo", uid="both-uid")

        # Test filter - need to create proper admin instance and request
        factory = RequestFactory()
        request = factory.get("/admin/users/user/", {"auth_type": "oidc"})
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        # The params dict tracks which params are used by filters
        params = request.GET.copy()
        filter_instance = AuthenticationTypeFilter(request, params, User, user_admin)
        # Only query the test users we created
        test_users = User.objects.filter(username__in=["local_user", "oidc_user", "both_user"])
        queryset = filter_instance.queryset(request, test_users)
        usernames = list(queryset.values_list("username", flat=True))

        assert "local_user" not in usernames
        assert "oidc_user" in usernames
        assert "both_user" not in usernames

    def test_queryset_filter_both(self):
        """Test filtering for users with both auth methods."""
        # Create users with different auth types
        user_local = get_user(username="local_user")
        user_local.set_password("SecureP@ssw0rd123")
        user_local.save()

        user_oidc = get_user(username="oidc_user")
        user_oidc.set_unusable_password()
        user_oidc.save()
        UserSocialAuth.objects.create(user=user_oidc, provider="tunnistamo", uid="oidc-uid")

        user_both = get_user(username="both_user")
        user_both.set_password("SecureP@ssw0rd456")
        user_both.save()
        UserSocialAuth.objects.create(user=user_both, provider="tunnistamo", uid="both-uid")

        # Test filter - need to create proper admin instance and request
        factory = RequestFactory()
        request = factory.get("/admin/users/user/", {"auth_type": "both"})
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        # The params dict tracks which params are used by filters
        params = request.GET.copy()
        filter_instance = AuthenticationTypeFilter(request, params, User, user_admin)
        # Only query the test users we created
        test_users = User.objects.filter(username__in=["local_user", "oidc_user", "both_user"])
        queryset = filter_instance.queryset(request, test_users)
        usernames = list(queryset.values_list("username", flat=True))

        assert "local_user" not in usernames
        assert "oidc_user" not in usernames
        assert "both_user" in usernames

    def test_queryset_filter_none(self):
        """Test filtering for users with no auth methods."""
        # Create users with different auth types
        user_local = get_user(username="local_user")
        user_local.set_password("SecureP@ssw0rd123")
        user_local.save()

        user_none = get_user(username="none_user")
        user_none.set_unusable_password()
        user_none.save()

        # Test filter - need to create proper admin instance and request
        factory = RequestFactory()
        request = factory.get("/admin/users/user/", {"auth_type": "none"})
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        # The params dict tracks which params are used by filters
        params = request.GET.copy()
        filter_instance = AuthenticationTypeFilter(request, params, User, user_admin)
        # Only query the test users we created
        test_users = User.objects.filter(username__in=["local_user", "none_user"])
        queryset = filter_instance.queryset(request, test_users)
        usernames = list(queryset.values_list("username", flat=True))

        assert "local_user" not in usernames
        assert "none_user" in usernames


@pytest.mark.django_db
class TestUserAdmin:
    """Tests for UserAdmin display and functionality."""

    def test_auth_type_display_local(self):
        """Test auth_type_display method for local-only user."""
        user = get_user()
        user.set_password("SecureP@ssw0rd123")
        user.save()

        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        display = user_admin.auth_type_display(user)

        assert "Local" in display
        assert "red" in display

    def test_auth_type_display_oidc(self):
        """Test auth_type_display method for OIDC-only user."""
        user = get_user()
        user.set_unusable_password()
        user.save()
        UserSocialAuth.objects.create(user=user, provider="tunnistamo", uid="test-uid")

        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        display = user_admin.auth_type_display(user)

        assert "Azure AD" in display
        assert "green" in display

    def test_auth_type_display_both(self):
        """Test auth_type_display method for user with both auth methods."""
        user = get_user()
        user.set_password("SecureP@ssw0rd123")
        user.save()
        UserSocialAuth.objects.create(user=user, provider="tunnistamo", uid="test-uid")

        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        display = user_admin.auth_type_display(user)

        assert "Both" in display
        assert "chocolate" in display

    def test_auth_type_display_none(self):
        """Test auth_type_display method for user with no auth methods."""
        user = get_user()
        user.set_unusable_password()
        user.save()

        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        display = user_admin.auth_type_display(user)

        assert "None" in display

    def test_get_queryset_prefetches_social_auth(self):
        """Test that get_queryset prefetches social_auth for optimization."""
        factory = RequestFactory()
        request = factory.get("/admin/users/user/")
        request.user = get_user(admin=True)

        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        queryset = user_admin.get_queryset(request)

        # Check that prefetch_related was called
        # _prefetch_related_lookups can contain strings or Prefetch objects
        prefetch_lookups = queryset._prefetch_related_lookups
        assert "social_auth" in prefetch_lookups or any(
            getattr(p, "prefetch_to", None) == "social_auth" for p in prefetch_lookups
        )

    def test_auth_type_in_list_display(self):
        """Test that auth_type_display is in list_display."""
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)

        assert "auth_type_display" in user_admin.list_display

    def test_auth_type_in_readonly_fields(self):
        """Test that auth_type_display is in readonly_fields."""
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)

        assert "auth_type_display" in user_admin.readonly_fields

    def test_auth_filter_in_list_filter(self):
        """Test that AuthenticationTypeFilter is in list_filter."""
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)

        assert AuthenticationTypeFilter in user_admin.list_filter
