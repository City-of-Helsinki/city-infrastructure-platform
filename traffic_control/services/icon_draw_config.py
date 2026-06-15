from dataclasses import dataclass

from django.db import models

from map.models import IconDrawingConfig


@dataclass
class IconDrawConfigValues:
    """Resolved icon drawing configuration values.

    Attributes:
        icons_relative_url (str): Relative URL path to the icon assets.
        scale (float): Icon scale factor.
        image_type (str): Icon image format (e.g. 'svg', 'png').
        png_size (int): Icon size in pixels (used for PNG icons).
    """

    icons_relative_url: str
    scale: float
    image_type: str
    png_size: int


def get_active_icon_drawing_config() -> IconDrawingConfig | None:
    """Fetch the single enabled IconDrawingConfig row from the database.

    Returns:
        IconDrawingConfig | None: The enabled config instance, or None if not found.
    """
    try:
        return IconDrawingConfig.objects.get(enabled=True)
    except models.ObjectDoesNotExist:
        return None


def get_icon_draw_config_values() -> IconDrawConfigValues:
    """Return resolved icon drawing config values with a single DB query.

    Falls back to IconDrawingConfig defaults when no enabled config exists.

    Returns:
        IconDrawConfigValues: Dataclass holding all icon config properties.
    """
    config = get_active_icon_drawing_config()
    if config:
        return IconDrawConfigValues(
            icons_relative_url=config.icons_relative_url,
            scale=config.scale,
            image_type=config.image_type,
            png_size=config.png_size,
        )
    return IconDrawConfigValues(
        icons_relative_url=IconDrawingConfig.DEFAULT_ICON_URL,
        scale=IconDrawingConfig.DEFAULT_ICON_SCALE,
        image_type="svg",
        png_size=IconDrawingConfig.DEFAULT_ICON_SIZE,
    )
