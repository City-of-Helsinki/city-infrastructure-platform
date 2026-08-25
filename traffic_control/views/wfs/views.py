from django.conf import settings
from django.db import transaction
from django.utils.decorators import method_decorator
from gisserver.features import ServiceDescription
from gisserver.operations import wfs20
from gisserver.views import WFSView

from city_furniture.views.wfs import FurnitureSignpostPlanFeatureType, FurnitureSignpostRealFeatureType
from traffic_control.views.wfs import (
    AdditionalSignPlanFeatureType,
    AdditionalSignRealFeatureType,
    MountPlanCentroidFeatureType,
    MountPlanFeatureType,
    MountRealCentroidFeatureType,
    MountRealFeatureType,
    PlanFeatureType,
    SignpostPlanFeatureType,
    SignpostRealFeatureType,
    TrafficSignPlanFeatureType,
    TrafficSignRealFeatureType,
)
from traffic_control.views.wfs.common import CustomGetFeature


# GetFeature responses are streamed with StreamingHttpResponse while a server-side (named)
# cursor is still open. With the project-wide ATOMIC_REQUESTS the transaction is committed as
# soon as the view returns, which closes that cursor before the response body is consumed
# ("named cursor isn't valid anymore"). WFS is read-only, so opting out of ATOMIC_REQUESTS
# keeps the connection in autocommit and the cursor alive for the whole stream.
@method_decorator(transaction.non_atomic_requests, name="dispatch")
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
        SignpostRealFeatureType,
        SignpostPlanFeatureType,
        MountRealFeatureType,
        MountRealCentroidFeatureType,
        MountPlanFeatureType,
        MountPlanCentroidFeatureType,
        PlanFeatureType,
    ]
