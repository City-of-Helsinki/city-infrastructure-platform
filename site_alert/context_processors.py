from .models import SiteAlert


def site_alerts(request):
    # Get the list of dismissed alert IDs from the user's session
    # Works for both logged-in and anonymous users

    try:
        dismissed_ids = request.session.get("dismissed_alerts", [])

        # Fetch active alerts that haven't been dismissed
        active_alerts = SiteAlert.objects.active().exclude(id__in=dismissed_ids).order_by("-level", "-created_at")
        return {"site_alerts": active_alerts}
    # Don't break non-session requests
    except AttributeError:
        active_alerts = SiteAlert.objects.active().order_by("-level", "-created_at")
        return {"site_alerts": active_alerts}
