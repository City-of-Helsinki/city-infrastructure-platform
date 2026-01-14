from django import template

from ..models import SiteAlert

register = template.Library()


@register.inclusion_tag("site_alert/includes/alert_box.html", takes_context=True)
def render_site_alerts(context):
    request = context["request"]
    dismissed_ids = request.session.get("dismissed_alerts", [])
    active_alerts = SiteAlert.objects.filter(is_active=True).exclude(id__in=dismissed_ids).order_by("-created_at")

    return {
        "alerts": active_alerts,
        "request": request,
    }
