from copy import deepcopy

from gisserver.features import FeatureField, FeatureType

from traffic_control.models import Plan
from traffic_control.views.wfs.common import (
    DEFAULT_CRS,
    OTHER_CRS,
    SOURCE_CONTROLLED_MODEL_FIELDS,
    USER_CONTROLLED_MODEL_FIELDS,
)
from traffic_control.views.wfs.utils import ConvexHullLocationXsdElement

_fields = (
    [
        FeatureField("id", abstract="ID of the Plan."),
        FeatureField("location", xsd_class=ConvexHullLocationXsdElement, abstract="Location of the Plan."),
        FeatureField("name", abstract="Name of the Plan."),
        FeatureField("decision_id", abstract="Decision ID of the Plan."),
        FeatureField("diary_number", abstract="Diary numbger of the Plan."),
        FeatureField("drawing_numbers", abstract="Drawing numbers of the Plan."),
        FeatureField(
            "derive_location",
            abstract="Derive the plan location (geometry area) from the locations of related devices.",
        ),
        FeatureField("decision_date", abstract="Decision date of the Plan."),
        FeatureField("decision_url", abstract="URL to the decision of the Plan."),
    ]
    + deepcopy(SOURCE_CONTROLLED_MODEL_FIELDS)
    + deepcopy(USER_CONTROLLED_MODEL_FIELDS)
)

PlanFeatureType = FeatureType(
    crs=DEFAULT_CRS,
    other_crs=OTHER_CRS,
    queryset=Plan.objects.active(),
    fields=_fields,
)
