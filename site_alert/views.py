from django.http import JsonResponse
from django.views.decorators.http import require_POST


@require_POST
def dismiss_alert(request, alert_id):
    """Adds the alert_id to the session's dismissed list."""
    if "dismissed_alerts" not in request.session:
        request.session["dismissed_alerts"] = []

    dismissed_list = request.session["dismissed_alerts"]
    if alert_id not in dismissed_list:
        dismissed_list.append(alert_id)
        request.session["dismissed_alerts"] = dismissed_list
        request.session.modified = True

    return JsonResponse({"status": "ok"})
