import json

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.translation import ugettext as _

from map.models import Layer


@staff_member_required
def map_view(request):
    language_code = request.LANGUAGE_CODE
    basemaps = list(
        Layer.objects.filter(is_basemap=True).values_list(
            "identifier", f"name_{language_code}"
        )
    )
    overlays = list(
        Layer.objects.filter(is_basemap=False).values_list(
            "identifier", f"name_{language_code}"
        )
    )
    layer_config = {
        "basemap": {"title": _("Basemaps"), "layers": basemaps},
        "overlay": {"title": _("Overlays"), "layers": overlays},
    }
    map_config = {
        "layerConfig": layer_config,
        "overlaySourceUrl": settings.OVERLAY_SOURCE_URL,
    }
    return render(request, "map/map_view.html", {"map_config": json.dumps(map_config)})
