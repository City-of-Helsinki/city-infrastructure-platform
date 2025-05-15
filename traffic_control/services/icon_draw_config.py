from django.db import models

from map.models import IconDrawingConfig


def get_active_icon_drawing_config():
    try:
        return IconDrawingConfig.objects.get(active=True)
    except models.ObjectDoesNotExist:
        return None


def get_icons_relative_url():
    config = get_active_icon_drawing_config()
    return get_active_icon_drawing_config().icons_relative_url if config else IconDrawingConfig.DEFAULT_ICON_URL


def get_icons_scale():
    config = get_active_icon_drawing_config()
    return get_active_icon_drawing_config().scale if config else IconDrawingConfig.DEFAULT_ICON_SCALE


def get_icons_type():
    config = get_active_icon_drawing_config()
    return get_active_icon_drawing_config().image_type if config else "svg"
