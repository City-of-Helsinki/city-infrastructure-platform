from django import template

register = template.Library()


@register.inclusion_tag("site_alert/includes/alert_box.html", takes_context=True)
def render_site_alerts(context):
    request = context["request"]
    return {
        "site_alerts": context.get("site_alerts", []),
        "csrf_token": context.get("csrf_token", None),
        "request": request,
    }
