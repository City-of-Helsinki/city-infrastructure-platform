from django.contrib import admin
from social_django.admin import UserSocialAuth

from traffic_control.admin.additional_sign import AdditionalSignPlanAdmin, AdditionalSignRealAdmin
from traffic_control.admin.affect_area import CoverageAreaAdmin, CoverageAreaCategoryAdmin
from traffic_control.admin.audit_log import AuditLogHistoryAdmin
from traffic_control.admin.barrier import (
    BarrierPlanAdmin,
    BarrierPlanFileInline,
    BarrierRealAdmin,
    BarrierRealFileInline,
)
from traffic_control.admin.common import OperationTypeAdmin
from traffic_control.admin.mount import (
    MountPlanAdmin,
    MountPlanFileInline,
    MountRealAdmin,
    MountRealFileInline,
    PortalTypeAdmin,
)
from traffic_control.admin.owner import OwnerAdmin
from traffic_control.admin.parking_zone_update_info import ParkingZoneUpdateInfoAdmin
from traffic_control.admin.plan import PlanAdmin
from traffic_control.admin.road_marking import (
    RoadMarkingPlanAdmin,
    RoadMarkingPlanFileInline,
    RoadMarkingRealAdmin,
    RoadMarkingRealFileInline,
)
from traffic_control.admin.signpost import (
    SignpostPlanAdmin,
    SignpostPlanFileInline,
    SignpostRealAdmin,
    SignpostRealFileInline,
)
from traffic_control.admin.traffic_light import (
    TrafficLightPlanAdmin,
    TrafficLightPlanFileInline,
    TrafficLightRealAdmin,
    TrafficLightRealFileInline,
)
from traffic_control.admin.traffic_sign import (
    OrderedTrafficSignRealInline,
    TrafficSignPlanAdmin,
    TrafficSignPlanFileInline,
    TrafficSignRealAdmin,
    TrafficSignRealFileInline,
)

admin.site.unregister(UserSocialAuth)
