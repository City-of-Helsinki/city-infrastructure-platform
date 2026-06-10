"""OSM tile proxy view for the Django admin map widget.

Proxies OpenStreetMap tile requests through the Django server so that
the browser never contacts tile.openstreetmap.org directly.  This
eliminates the Firefox-specific 403 that occurs when ol.source.OSM uses
``crossOrigin='anonymous'``, which causes Firefox to add an
``Origin: http://localhost:8000`` header.  OSM's tile CDN blocks CORS
requests from private/localhost origins while allowing plain (non-CORS)
browser requests.  Chrome is unaffected because it served the tiles from
its cache before the CORS mode was active.

The proxy is restricted to authenticated staff members and is only
reachable from the admin map widget.
"""

import logging

import requests
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)

_OSM_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
_REQUEST_TIMEOUT_SECONDS = 10
# OSM tile-usage policy requires a descriptive User-Agent that identifies
# the application and provides a way to contact the operator.
# See https://operations.osmfoundation.org/policies/tiles/ for full policy
_USER_AGENT = (
    "CityInfrastructurePlatform/1.0 "
    "(https://github.com/City-of-Helsinki/city-infrastructure-platform)"
)


@staff_member_required
def osm_tile_proxy(request: HttpRequest, z: int, x: int, y: int) -> HttpResponse:
    """Proxy a single OSM raster tile to the admin map widget.

    Fetches the tile server-side so the browser makes a same-origin
    request, avoiding the CORS ``Origin`` header that triggers 403 on
    Firefox.

    Args:
        request (HttpRequest): The incoming Django request (must be from
            an authenticated staff member).
        z (int): Zoom level.
        x (int): Tile column.
        y (int): Tile row.

    Returns:
        HttpResponse: The proxied tile PNG with its original Content-Type,
            or an error response with the upstream status code.
    """
    tile_url = _OSM_TILE_URL.format(z=z, x=x, y=y)
    try:
        upstream = requests.get(
            tile_url,
            headers={"User-Agent": _USER_AGENT},
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.warning("OSM tile proxy failed for %s: %s", tile_url, exc)
        return HttpResponse(status=502)

    content_type = upstream.headers.get("Content-Type", "image/png")
    return HttpResponse(upstream.content, content_type=content_type, status=upstream.status_code)

