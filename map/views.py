import logging

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _

from traffic_control.services.azure import get_azure_storage_base_url
from traffic_control.services.icon_draw_config import get_icons_relative_url, get_icons_scale, get_icons_type

from .models import FeatureTypeEditMapping, Layer

logger = logging.getLogger("map")

ALLOWED_MAP_LANGUAGE_CODES = ["en", "fi", "sv"]
"""Layer model needs to have field name_<language_code>"""


@staff_member_required
def map_view(request):
    return render(request, "index.html")


def map_config(request):
    language_code = _get_language_code(request)
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
                "extra_feature_info": _get_extra_feature_info(language_code, overlay),
            }
        )

    icon_options = settings.STORAGES["icons"]["OPTIONS"]
    traffic_sign_icons_url = f"{get_azure_storage_base_url(icon_options)}{get_icons_relative_url()}"
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
        "icon_scale": get_icons_scale(),
        "icon_type": get_icons_type(),
        "featureTypeEditNameMapping": FeatureTypeEditMapping.get_featuretype_edit_name_mapping(),
        "address_search_base_url": settings.ADDRESS_SEARCH_BASE_URL,
    }
    return JsonResponse(config)


def _get_extra_feature_info(language_code: str, layer: Layer) -> dict:
    layer_extra_info = layer.extra_feature_info
    localized_extra_info = {}
    if layer_extra_info:
        for k, v in layer_extra_info.items():
            localized_title = v.get(f"title_{language_code}", None)
            extra_field_data = {"order": v.get("order", 0)}
            if not localized_title:
                logger.warning(
                    f"localized title not found from layer info for field {k}: {v}: {language_code},"
                    f" defaulting to fi"
                )
                extra_field_data["title"] = v.get("title_fi")
            else:
                extra_field_data["title"] = localized_title
            localized_extra_info[k] = extra_field_data
    return localized_extra_info


def _get_overview_image_extent():
    """In the hardcoded png file 1 px means 32 meters in real world.
    Resolution of the image is 704x704
    Coordinates for top left corner are 25490088.0, 6687593.0
    """
    return [25490088.0, 6687593.0 - 32 * 704, 25490088 + 32 * 704, 6687593.0]


def _get_language_code(request):
    """Get language code from request. If not allowed then defaults to en."""
    language_from_request = request.LANGUAGE_CODE
    if language_from_request not in ALLOWED_MAP_LANGUAGE_CODES:
        logger.warning(f"Not allowed: {language_from_request} defaulting to fi")
        return "fi"
    return language_from_request
