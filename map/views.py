from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _

from .models import FeatureTypeEditMapping, Layer


@staff_member_required
def map_view(request):
    return render(request, "index.html")


def map_config(request):
    language_code = request.LANGUAGE_CODE
    basemaps = []
    for basemap in Layer.objects.filter(is_basemap=True):
        basemaps.append(
            {
                "identifier": basemap.identifier,
                "name": getattr(basemap, f"name_{language_code}"),
            }
        )

    overlays = []
    for overlay in Layer.objects.filter(is_basemap=False):
        overlays.append(
            {
                "identifier": overlay.identifier,
                "name": getattr(overlay, f"name_{language_code}"),
                "app_name": overlay.app_name,
                "filter_fields": overlay.filter_fields.split(",") if overlay.filter_fields != "" else [],
                "use_traffic_sign_icons": overlay.use_traffic_sign_icons,
                "clustered": overlay.clustered,
            }
        )

    traffic_sign_icons_url = f"{request.build_absolute_uri(settings.STATIC_URL)}traffic_control/svg/traffic_sign_icons/"
    config = {
        "basemapConfig": {
            "name": _("Basemaps"),
            "layers": basemaps,
            "sourceUrl": settings.BASEMAP_SOURCE_URL,
        },
        "overlayConfig": {
            "name": _("Overlays"),
            "layers": overlays,
            "sourceUrl": request.build_absolute_uri("/")[:-1] + reverse("wfs-city-infrastructure"),
        },
        "overviewConfig": {
            "imageUrl": f"{request.build_absolute_uri(settings.STATIC_URL)}"
            f"traffic_control/png/map/cityinfra_overview_map-704x704.png",
            "imageExtent": _get_overview_image_extent(),
        },
        "traffic_sign_icons_url": traffic_sign_icons_url,
        "featureTypeEditNameMapping": FeatureTypeEditMapping.get_featuretype_edit_name_mapping(),
    }
    return JsonResponse(config)


def _get_overview_image_extent():
    """In the hardcoded png file 1 px means 32 meters in real world.
    Resolution of the image is 704x704
    Coordinates for top left corner are 25490088.0, 6687593.0
    """
    return [25490088.0, 6687593.0 - 32 * 704, 25490088 + 32 * 704, 6687593.0]
