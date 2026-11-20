from typing import Any

from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import SESSION_KEY
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _, ngettext
from django.views.generic import TemplateView

from users.models import User
from users.sessions import count_active_sessions, list_sessions, terminate_other_sessions, terminate_session


class AdminTemplateView(TemplateView):
    title: str

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            **admin.site.each_context(self.request),
            "title": self.title,
            "user": self.request.user,
        }


class SuperuserRequiredMixin:
    """Allows access only to superusers. Combine with ``staff_member_required`` for the login redirect."""

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Rejects users who are not superusers.

        Args:
            request (HttpRequest): The request.
            *args (Any): Positional URL arguments.
            **kwargs (Any): Keyword URL arguments.

        Returns:
            HttpResponse: The response of the view.

        Raises:
            PermissionDenied: If the user is not a superuser.
        """
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


@method_decorator(staff_member_required, name="dispatch")
class MyAccountView(AdminTemplateView):
    template_name = "admin/my_account.html"
    title = _("My account")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Adds the number of the user's active sessions to the context.

        Args:
            **kwargs (Any): Keyword URL arguments.

        Returns:
            dict[str, Any]: The template context.
        """
        return {**super().get_context_data(**kwargs), "active_session_count": count_active_sessions(self.request.user)}


class SessionManagementView(AdminTemplateView):
    """Lists a user's active sessions and lets the requester terminate them, except the current one."""

    template_name = "admin/user_sessions.html"

    def get_target_user(self) -> User:
        """Returns the user whose sessions are managed.

        Returns:
            User: The user.

        Raises:
            NotImplementedError: If a subclass does not override this method.
        """
        raise NotImplementedError

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Adds the target user and their sessions to the context.

        Args:
            **kwargs (Any): Keyword URL arguments.

        Returns:
            dict[str, Any]: The template context.
        """
        target_user = self.get_target_user()
        return {
            **super().get_context_data(**kwargs),
            "target_user": target_user,
            "is_own_sessions": target_user == self.request.user,
            "sessions": list_sessions(target_user, self.request.session.session_key),
        }

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Terminates one session or all sessions except the current one.

        Args:
            request (HttpRequest): The request.
            *args (Any): Positional URL arguments.
            **kwargs (Any): Keyword URL arguments.

        Returns:
            HttpResponse: A redirect back to the session list.

        Raises:
            PermissionDenied: If the request was not authenticated with its session, for example with an API
                token. Then the current session would not be known and could be terminated by mistake.
        """
        if request.session.get(SESSION_KEY) != str(request.user.pk):
            raise PermissionDenied
        current_key = request.session.session_key
        target_user = self.get_target_user()
        if request.POST.get("action") == "terminate_others":
            count = terminate_other_sessions(target_user, current_key, terminated_by=request.user)
            message = ngettext("%(count)d session was terminated.", "%(count)d sessions were terminated.", count)
            messages.success(request, message % {"count": count})
        elif terminate_session(target_user, request.POST.get("session_id", ""), current_key, request.user):
            messages.success(request, _("The session was terminated."))
        else:
            messages.warning(request, _("The session was not found. It may already have ended."))
        return HttpResponseRedirect(request.get_full_path())


@method_decorator(staff_member_required, name="dispatch")
class MySessionsView(SessionManagementView):
    """Lets a staff user view and terminate their own sessions."""

    title = _("My sessions")

    def get_target_user(self) -> User:
        """Returns the requesting user.

        Returns:
            User: The requesting user.
        """
        return self.request.user


@method_decorator(staff_member_required, name="dispatch")
class UserSessionsView(SuperuserRequiredMixin, SessionManagementView):
    """Lets a superuser view and terminate the sessions of any user."""

    title = _("User sessions")

    def get_target_user(self) -> User:
        """Returns the user given in the URL.

        Returns:
            User: The user.
        """
        return get_object_or_404(User, pk=self.kwargs["user_id"])


@method_decorator(staff_member_required, name="dispatch")
class AllUserSessionsView(SuperuserRequiredMixin, AdminTemplateView):
    """Lists, for superusers, all users who have active sessions and their session counts."""

    template_name = "admin/all_user_sessions.html"
    title = _("Active sessions of all users")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Adds the users who have active sessions, with their session counts, to the context.

        Args:
            **kwargs (Any): Keyword URL arguments.

        Returns:
            dict[str, Any]: The template context.
        """
        active = Q(sessions__expire_date__gt=timezone.now())
        users = (
            User.objects.annotate(active_session_count=Count("sessions", filter=active))
            .filter(active_session_count__gt=0)
            .order_by("username")
        )
        return {**super().get_context_data(**kwargs), "users_with_sessions": users}


@method_decorator(staff_member_required, name="dispatch")
class FeatureDisabledView(AdminTemplateView):
    template_name = "admin/disabled_feature.html"
    title = _("Disabled feature")
