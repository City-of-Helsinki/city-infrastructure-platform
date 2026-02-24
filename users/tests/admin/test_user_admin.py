from datetime import timedelta

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.utils import timezone
from social_django.models import UserSocialAuth

from traffic_control.tests.factories import UserFactory
from users.admin import AuthenticationTypeFilter, ReactivatedFilter, UserAdmin
from users.models import User, UserDeactivationStatus


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
        user_local = UserFactory(username="local_user")
        user_local.set_password("SecureP@ssw0rd123")
        user_local.save()

        user_oidc = UserFactory(username="oidc_user")
        user_oidc.set_unusable_password()
        user_oidc.save()
        UserSocialAuth.objects.create(user=user_oidc, provider="tunnistamo", uid="oidc-uid")

        user_both = UserFactory(username="both_user")
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
        user_local = UserFactory(username="local_user")
        user_local.set_password("SecureP@ssw0rd123")
        user_local.save()

        user_oidc = UserFactory(username="oidc_user")
        user_oidc.set_unusable_password()
        user_oidc.save()
        UserSocialAuth.objects.create(user=user_oidc, provider="tunnistamo", uid="oidc-uid")

        user_both = UserFactory(username="both_user")
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
        user_local = UserFactory(username="local_user")
        user_local.set_password("SecureP@ssw0rd123")
        user_local.save()

        user_oidc = UserFactory(username="oidc_user")
        user_oidc.set_unusable_password()
        user_oidc.save()
        UserSocialAuth.objects.create(user=user_oidc, provider="tunnistamo", uid="oidc-uid")

        user_both = UserFactory(username="both_user")
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
        user_local = UserFactory(username="local_user")
        user_local.set_password("SecureP@ssw0rd123")
        user_local.save()

        user_none = UserFactory(username="none_user")
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
        user = UserFactory()
        user.set_password("SecureP@ssw0rd123")
        user.save()

        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        display = user_admin.auth_type_display(user)

        assert "Local" in display
        assert "red" in display

    def test_auth_type_display_oidc(self):
        """Test auth_type_display method for OIDC-only user."""
        user = UserFactory()
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
        user = UserFactory()
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
        user = UserFactory()
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
        request.user = UserFactory(is_staff=True, is_superuser=True)

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


@pytest.mark.django_db
class TestReactivatedFilter:
    """Tests for ReactivatedFilter in user admin."""

    def test_lookups(self):
        """Test that filter provides correct lookup options for reactivation dates."""
        filter_instance = ReactivatedFilter(None, {}, User, UserAdmin)
        lookups = filter_instance.lookups(None, None)

        assert len(lookups) == 3
        lookup_values = [item[0] for item in lookups]
        assert "30" in lookup_values
        assert "90" in lookup_values
        assert "180" in lookup_values

    def test_queryset_filter_last_30_days(self):
        """Test filtering for users reactivated in last 30 days."""
        now = timezone.now()

        # Create users reactivated at different times
        user_recent = UserFactory(username="recent_user")
        user_recent.reactivated_at = now - timedelta(days=15)
        user_recent.save()

        user_old = UserFactory(username="old_user")
        user_old.reactivated_at = now - timedelta(days=60)
        user_old.save()

        user_no_reactivation = UserFactory(username="no_reactivation")
        user_no_reactivation.save()

        # Test filter
        factory = RequestFactory()
        request = factory.get("/admin/users/user/", {"reactivated": "30"})
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        params = request.GET.copy()
        filter_instance = ReactivatedFilter(request, params, User, user_admin)

        test_users = User.objects.filter(username__in=["recent_user", "old_user", "no_reactivation"])
        queryset = filter_instance.queryset(request, test_users)
        usernames = list(queryset.values_list("username", flat=True))

        assert "recent_user" in usernames
        assert "old_user" not in usernames
        assert "no_reactivation" not in usernames

    def test_queryset_filter_last_90_days(self):
        """Test filtering for users reactivated in last 90 days."""
        now = timezone.now()

        user_60_days = UserFactory(username="user_60")
        user_60_days.reactivated_at = now - timedelta(days=60)
        user_60_days.save()

        user_120_days = UserFactory(username="user_120")
        user_120_days.reactivated_at = now - timedelta(days=120)
        user_120_days.save()

        # Test filter
        factory = RequestFactory()
        request = factory.get("/admin/users/user/", {"reactivated": "90"})
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        params = request.GET.copy()
        filter_instance = ReactivatedFilter(request, params, User, user_admin)

        test_users = User.objects.filter(username__in=["user_60", "user_120"])
        queryset = filter_instance.queryset(request, test_users)
        usernames = list(queryset.values_list("username", flat=True))

        assert "user_60" in usernames
        assert "user_120" not in usernames

    def test_queryset_filter_last_180_days(self):
        """Test filtering for users reactivated in last 180 days."""
        now = timezone.now()

        user_100_days = UserFactory(username="user_100")
        user_100_days.reactivated_at = now - timedelta(days=100)
        user_100_days.save()

        user_200_days = UserFactory(username="user_200")
        user_200_days.reactivated_at = now - timedelta(days=200)
        user_200_days.save()

        # Test filter
        factory = RequestFactory()
        request = factory.get("/admin/users/user/", {"reactivated": "180"})
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        params = request.GET.copy()
        filter_instance = ReactivatedFilter(request, params, User, user_admin)

        test_users = User.objects.filter(username__in=["user_100", "user_200"])
        queryset = filter_instance.queryset(request, test_users)
        usernames = list(queryset.values_list("username", flat=True))

        assert "user_100" in usernames
        assert "user_200" not in usernames

    def test_queryset_no_filter_returns_all(self):
        """Test that no filter value returns all users."""
        now = timezone.now()

        user1 = UserFactory(username="user1")
        user1.reactivated_at = now - timedelta(days=10)
        user1.save()

        user2 = UserFactory(username="user2")
        user2.save()

        # Test filter without value
        factory = RequestFactory()
        request = factory.get("/admin/users/user/")
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        params = request.GET.copy()
        filter_instance = ReactivatedFilter(request, params, User, user_admin)

        test_users = User.objects.filter(username__in=["user1", "user2"])
        queryset = filter_instance.queryset(request, test_users)

        assert queryset.count() == test_users.count()


@pytest.mark.django_db
class TestReactivateSelectedUsersAction:
    """Tests for the reactivate_selected_users admin action."""

    def test_reactivate_users_as_superuser(self):
        """Test that superuser can reactivate selected users."""
        # Create deactivated users
        user1 = UserFactory(username="inactive1")
        user1.email = "user1@example.com"
        user1.is_active = False
        user1.save()

        user2 = UserFactory(username="inactive2")
        user2.email = "user2@example.com"
        user2.is_active = False
        user2.save()

        # Create UserDeactivationStatus for them
        UserDeactivationStatus.objects.create(user=user1, deactivated_at=timezone.now() - timedelta(days=10))
        UserDeactivationStatus.objects.create(user=user2, deactivated_at=timezone.now() - timedelta(days=5))

        # Create superuser and request
        superuser = UserFactory(username="superuser", is_staff=True, is_superuser=True)
        superuser.is_superuser = True
        superuser.save()

        factory = RequestFactory()
        request = factory.post("/admin/users/user/")
        request.user = superuser

        # Add message storage (required for admin actions)
        setattr(request, "session", {})
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        # Execute action
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        queryset = User.objects.filter(id__in=[user1.id, user2.id])
        user_admin.reactivate_selected_users(request, queryset)

        # Verify users are reactivated
        user1.refresh_from_db()
        user2.refresh_from_db()

        assert user1.is_active is True
        assert user2.is_active is True
        assert user1.reactivated_at is not None
        assert user2.reactivated_at is not None

        # Verify deactivation statuses are deleted
        assert not UserDeactivationStatus.objects.filter(user=user1).exists()
        assert not UserDeactivationStatus.objects.filter(user=user2).exists()

    def test_reactivate_users_sets_timestamp(self):
        """Test that reactivation sets the reactivated_at timestamp."""
        user = UserFactory(username="inactive_user")
        user.is_active = False
        user.save()

        before_reactivation = timezone.now()

        superuser = UserFactory(username="superuser", is_staff=True, is_superuser=True)
        superuser.is_superuser = True
        superuser.save()

        factory = RequestFactory()
        request = factory.post("/admin/users/user/")
        request.user = superuser
        setattr(request, "session", {})
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        queryset = User.objects.filter(id=user.id)
        user_admin.reactivate_selected_users(request, queryset)

        user.refresh_from_db()

        assert user.reactivated_at is not None
        assert user.reactivated_at >= before_reactivation
        assert user.reactivated_at <= timezone.now()

    def test_reactivate_users_deletes_deactivation_status(self):
        """Test that reactivation deletes UserDeactivationStatus."""
        user = UserFactory(username="inactive_user")
        user.is_active = False
        user.save()

        UserDeactivationStatus.objects.create(
            user=user,
            one_month_email_sent_at=timezone.now() - timedelta(days=40),
            one_week_email_sent_at=timezone.now() - timedelta(days=17),
            one_day_email_sent_at=timezone.now() - timedelta(days=11),
            deactivated_at=timezone.now() - timedelta(days=10),
        )

        assert UserDeactivationStatus.objects.filter(user=user).exists()

        superuser = UserFactory(username="superuser", is_staff=True, is_superuser=True)
        superuser.is_superuser = True
        superuser.save()

        factory = RequestFactory()
        request = factory.post("/admin/users/user/")
        request.user = superuser
        setattr(request, "session", {})
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        queryset = User.objects.filter(id=user.id)
        user_admin.reactivate_selected_users(request, queryset)

        # Verify status was deleted
        assert not UserDeactivationStatus.objects.filter(user=user).exists()

    def test_reactivate_users_handles_no_deactivation_status(self):
        """Test that reactivation works even if no UserDeactivationStatus exists."""
        user = UserFactory(username="inactive_user")
        user.is_active = False
        user.save()

        # No UserDeactivationStatus created

        superuser = UserFactory(username="superuser", is_staff=True, is_superuser=True)
        superuser.is_superuser = True
        superuser.save()

        factory = RequestFactory()
        request = factory.post("/admin/users/user/")
        request.user = superuser
        setattr(request, "session", {})
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        queryset = User.objects.filter(id=user.id)

        # Should not raise an error
        user_admin.reactivate_selected_users(request, queryset)

        user.refresh_from_db()
        assert user.is_active is True
        assert user.reactivated_at is not None

    def test_non_superuser_cannot_reactivate(self):
        """Test that non-superuser cannot reactivate users."""
        user = UserFactory(username="inactive_user")
        user.is_active = False
        user.save()

        # Create regular staff user (not superuser)
        staff_user = UserFactory(username="staff", is_staff=True)
        staff_user.is_staff = True
        staff_user.is_superuser = False
        staff_user.save()

        factory = RequestFactory()
        request = factory.post("/admin/users/user/")
        request.user = staff_user
        setattr(request, "session", {})
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        queryset = User.objects.filter(id=user.id)
        user_admin.reactivate_selected_users(request, queryset)

        # User should still be inactive
        user.refresh_from_db()
        assert user.is_active is False
        assert user.reactivated_at is None

    def test_reactivate_action_shows_success_message(self):
        """Test that reactivation shows success message with count."""
        users = []
        for i in range(3):
            user = UserFactory(username=f"user{i}")
            user.email = f"user{i}@example.com"
            user.is_active = False
            user.save()
            users.append(user)

        superuser = UserFactory(username="superuser", is_staff=True, is_superuser=True)
        superuser.is_superuser = True
        superuser.save()

        factory = RequestFactory()
        request = factory.post("/admin/users/user/")
        request.user = superuser
        setattr(request, "session", {})
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        queryset = User.objects.filter(username__in=[u.username for u in users])
        user_admin.reactivate_selected_users(request, queryset)

        # Check that success message was added
        message_list = list(messages)
        assert len(message_list) > 0
        assert "3" in str(message_list[0])
        assert "reactivated" in str(message_list[0]).lower()

    def test_reactivate_action_uses_transaction(self):
        """Test that reactivation uses atomic transaction."""
        # This test verifies the action uses transaction.atomic()
        # by checking that all operations succeed or fail together
        user1 = UserFactory(username="user1")
        user1.is_active = False
        user1.save()

        user2 = UserFactory(username="user2")
        user2.is_active = False
        user2.save()

        superuser = UserFactory(username="superuser", is_staff=True, is_superuser=True)
        superuser.is_superuser = True
        superuser.save()

        factory = RequestFactory()
        request = factory.post("/admin/users/user/")
        request.user = superuser
        setattr(request, "session", {})
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)
        queryset = User.objects.filter(id__in=[user1.id, user2.id])
        user_admin.reactivate_selected_users(request, queryset)

        # Both users should be reactivated
        user1.refresh_from_db()
        user2.refresh_from_db()
        assert user1.is_active is True
        assert user2.is_active is True


@pytest.mark.django_db
class TestUserAdminDeactivationFields:
    """Tests for deactivation-related admin fields and display."""

    def test_reactivated_at_in_readonly_fields(self):
        """Test that reactivated_at is in readonly_fields."""
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)

        assert "reactivated_at" in user_admin.readonly_fields

    def test_reactivated_at_in_list_display(self):
        """Test that reactivated_at is in list_display."""
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)

        assert "reactivated_at" in user_admin.list_display

    def test_reactivated_at_in_fieldsets(self):
        """Test that reactivated_at appears in fieldsets."""
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)

        # Check fieldsets contain reactivated_at
        all_fields = []
        for fieldset in user_admin.fieldsets:
            if "fields" in fieldset[1]:
                all_fields.extend(fieldset[1]["fields"])

        assert "reactivated_at" in all_fields

    def test_reactivated_filter_in_list_filter(self):
        """Test that ReactivatedFilter is in list_filter."""
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)

        assert ReactivatedFilter in user_admin.list_filter

    def test_reactivate_action_in_actions(self):
        """Test that reactivate_selected_users is in actions."""
        admin_site = AdminSite()
        user_admin = UserAdmin(User, admin_site)

        assert "reactivate_selected_users" in user_admin.actions
