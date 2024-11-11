from django.conf import settings
from gisserver.features import ServiceDescription
from gisserver.operations import wfs20
from gisserver.views import WFSView

from city_furniture.views.wfs import FurnitureSignpostPlanFeatureType, FurnitureSignpostRealFeatureType
from traffic_control.views.wfs import (
    AdditionalSignPlanFeatureType,
    AdditionalSignRealFeatureType,
    MountPlanFeatureType,
    MountRealFeatureType,
    TrafficSignPlanFeatureType,
    TrafficSignRealFeatureType,
)
from traffic_control.views.wfs.common import CustomGetFeature


class CityInfrastructureWFSView(WFSView):
    service_description = ServiceDescription(title="City Infra WFS API")

    xml_namespace = f"http://{settings.HOSTNAME}/wfs"

    accept_operations = {
        "WFS": {
            "GetCapabilities": wfs20.GetCapabilities,
            "DescribeFeatureType": wfs20.DescribeFeatureType,
            "GetFeature": CustomGetFeature,
            "GetPropertyValue": wfs20.GetPropertyValue,
            "ListStoredQueries": wfs20.ListStoredQueries,
            "DescribeStoredQueries": wfs20.DescribeStoredQueries,
        }
    }

    feature_types = [
        FurnitureSignpostRealFeatureType,
        FurnitureSignpostPlanFeatureType,
        TrafficSignRealFeatureType,
        TrafficSignPlanFeatureType,
        AdditionalSignRealFeatureType,
        AdditionalSignPlanFeatureType,
        MountRealFeatureType,
        MountPlanFeatureType,
    ]
