from city_furniture.models.common import CityFurnitureColor


def get_city_furniture_color(name="Color", rgb="#FFFFFF"):
    return CityFurnitureColor.objects.get_or_create(name=name, defaults=dict(rgb=rgb))[0]
