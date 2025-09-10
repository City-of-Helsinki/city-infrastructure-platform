from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from city_furniture.models.common import CityFurnitureDeviceTypeIcon
from traffic_control.signal_utils import generate_pngs_on_svg_save


@receiver(post_save, sender=CityFurnitureDeviceTypeIcon)
def generate_city_furniture_device_type_icon_pngs(instance, **_kwargs):
    """
    Generates PNG files based on the uploaded SVG file after the model is saved.
    This process is asynchronous and non-blocking for the user.
    """
    generate_pngs_on_svg_save(instance=instance, png_folder=settings.CITY_FURNITURE_DEVICE_TYPE_PNG_ICON_DESTINATION)
