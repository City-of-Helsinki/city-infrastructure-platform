import pprint

from django.core.management.base import BaseCommand

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    BarrierPlan,
    BarrierReal,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficSignPlan,
    TrafficSignReal,
)


class Command(BaseCommand):
    help = "Print target model check. "

    MODEL_TO_TARGETMODEL_MAP = [
        (AdditionalSignPlan, DeviceTypeTargetModel.ADDITIONAL_SIGN),
        (AdditionalSignReal, DeviceTypeTargetModel.ADDITIONAL_SIGN),
        (BarrierPlan, DeviceTypeTargetModel.BARRIER),
        (BarrierReal, DeviceTypeTargetModel.BARRIER),
        (RoadMarkingPlan, DeviceTypeTargetModel.ROAD_MARKING),
        (RoadMarkingReal, DeviceTypeTargetModel.ROAD_MARKING),
        (SignpostPlan, DeviceTypeTargetModel.SIGNPOST),
        (SignpostReal, DeviceTypeTargetModel.SIGNPOST),
        (TrafficLightPlan, DeviceTypeTargetModel.TRAFFIC_LIGHT),
        (TrafficLightReal, DeviceTypeTargetModel.TRAFFIC_LIGHT),
        (TrafficSignPlan, DeviceTypeTargetModel.TRAFFIC_SIGN),
        (TrafficSignReal, DeviceTypeTargetModel.TRAFFIC_SIGN),
    ]

    def handle(self, *args, **options):
        print_mismatching_target_models(self.MODEL_TO_TARGETMODEL_MAP)


def get_mismatching_targets(model, expected_target):
    res = model.objects.exclude(device_type__target_model=expected_target).values_list(
        "device_type__target_model", "id", "device_type__id", "device_type__code"
    )
    results = {model: {}}
    for dt_model, obj_id, dt_id, dt_code in res:
        results[model].setdefault(dt_model, []).append((str(obj_id), str(dt_id), dt_code))
    pprint.pprint(results)


def print_mismatching_target_models(model_to_target):
    for model, expected_target in model_to_target:
        get_mismatching_targets(model, expected_target)
