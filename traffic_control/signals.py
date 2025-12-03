from auditlog.registry import auditlog
from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from traffic_control.models.common import TrafficControlDeviceTypeIcon
from traffic_control.signal_utils import delete_icon_files_on_row_delete, generate_pngs_on_svg_save


@receiver(post_save, sender=TrafficControlDeviceTypeIcon)
def generate_traffic_control_device_type_icon_pngs(instance, **_kwargs):
    """
    Generates PNG files based on the uploaded SVG file after the model is saved.
    This process is asynchronous and non-blocking for the user.
    """
    generate_pngs_on_svg_save(instance=instance, png_folder=settings.TRAFFIC_CONTROL_DEVICE_TYPE_PNG_ICON_DESTINATION)


@receiver(post_delete, sender=TrafficControlDeviceTypeIcon)
def delete_city_furniture_device_type_icon_files(instance, **_kwargs):
    """
    Deletes the SVG and associated PNG files from storage after the model is deleted.
    This process is asynchronous and non-blocking for the user.
    """
    delete_icon_files_on_row_delete(
        instance=instance, png_folder=settings.TRAFFIC_CONTROL_DEVICE_TYPE_PNG_ICON_DESTINATION
    )


# ============================================================================
# Audit log signal registration
# This must happen here in signals.py, not at module level in models files,
# to ensure proper initialization in multi-backend environments
# ============================================================================


def register_auditlog_signals():
    """
    Register custom audit log signals and auditlog models.
    Called during app initialization in apps.py ready() method.
    """
    from traffic_control.models.additional_sign import (
        AdditionalSignPlan,
        AdditionalSignPlanFile,
        AdditionalSignPlanReplacement,
        AdditionalSignReal,
        AdditionalSignRealFile,
    )
    from traffic_control.models.barrier import (
        BarrierPlan,
        BarrierPlanFile,
        BarrierPlanReplacement,
        BarrierReal,
        BarrierRealFile,
    )
    from traffic_control.models.mount import (
        MountPlan,
        MountPlanFile,
        MountPlanReplacement,
        MountReal,
        MountRealFile,
    )
    from traffic_control.models.road_marking import (
        RoadMarkingPlan,
        RoadMarkingPlanFile,
        RoadMarkingPlanReplacement,
        RoadMarkingReal,
        RoadMarkingRealFile,
    )
    from traffic_control.models.signpost import (
        SignpostPlan,
        SignpostPlanFile,
        SignpostPlanReplacement,
        SignpostReal,
        SignpostRealFile,
    )
    from traffic_control.models.traffic_light import (
        TrafficLightPlan,
        TrafficLightPlanFile,
        TrafficLightPlanReplacement,
        TrafficLightReal,
        TrafficLightRealFile,
    )
    from traffic_control.models.traffic_sign import (
        TrafficSignPlan,
        TrafficSignPlanFile,
        TrafficSignReal,
        TrafficSignRealFile,
    )
    from traffic_control.signal_utils import create_auditlog_signals_for_parent_model

    # Register custom signals BEFORE auditlog.register()
    # This ensures our custom signals fire before auditlog's signals
    create_auditlog_signals_for_parent_model(AdditionalSignRealFile, "additional_sign_real")
    create_auditlog_signals_for_parent_model(AdditionalSignPlanFile, "additional_sign_plan")
    create_auditlog_signals_for_parent_model(AdditionalSignReal, "parent")
    create_auditlog_signals_for_parent_model(AdditionalSignPlan, "parent")
    create_auditlog_signals_for_parent_model(TrafficSignRealFile, "traffic_sign_real")
    create_auditlog_signals_for_parent_model(TrafficSignPlanFile, "traffic_sign_plan")
    create_auditlog_signals_for_parent_model(SignpostRealFile, "signpost_real")
    create_auditlog_signals_for_parent_model(SignpostPlanFile, "signpost_plan")
    create_auditlog_signals_for_parent_model(TrafficLightRealFile, "traffic_light_real")
    create_auditlog_signals_for_parent_model(TrafficLightPlanFile, "traffic_light_plan")
    create_auditlog_signals_for_parent_model(BarrierRealFile, "barrier_real")
    create_auditlog_signals_for_parent_model(BarrierPlanFile, "barrier_plan")
    create_auditlog_signals_for_parent_model(RoadMarkingRealFile, "road_marking_real")
    create_auditlog_signals_for_parent_model(RoadMarkingPlanFile, "road_marking_plan")
    create_auditlog_signals_for_parent_model(MountRealFile, "mount_real")
    create_auditlog_signals_for_parent_model(MountPlanFile, "mount_plan")

    # Register models with auditlog AFTER our custom signals
    auditlog.register(AdditionalSignPlan)
    auditlog.register(AdditionalSignPlanFile)
    auditlog.register(AdditionalSignReal)
    auditlog.register(AdditionalSignRealFile)
    auditlog.register(AdditionalSignPlanReplacement)

    auditlog.register(TrafficSignPlan)
    auditlog.register(TrafficSignPlanFile)
    auditlog.register(TrafficSignReal)
    auditlog.register(TrafficSignRealFile)

    auditlog.register(SignpostPlan)
    auditlog.register(SignpostPlanFile)
    auditlog.register(SignpostReal)
    auditlog.register(SignpostRealFile)
    auditlog.register(SignpostPlanReplacement)

    auditlog.register(TrafficLightPlan)
    auditlog.register(TrafficLightPlanFile)
    auditlog.register(TrafficLightReal)
    auditlog.register(TrafficLightRealFile)
    auditlog.register(TrafficLightPlanReplacement)

    auditlog.register(BarrierPlan)
    auditlog.register(BarrierPlanFile)
    auditlog.register(BarrierReal)
    auditlog.register(BarrierRealFile)
    auditlog.register(BarrierPlanReplacement)

    auditlog.register(RoadMarkingPlan)
    auditlog.register(RoadMarkingPlanFile)
    auditlog.register(RoadMarkingReal)
    auditlog.register(RoadMarkingRealFile)
    auditlog.register(RoadMarkingPlanReplacement)

    auditlog.register(MountPlan)
    auditlog.register(MountPlanFile)
    auditlog.register(MountReal)
    auditlog.register(MountRealFile)
    auditlog.register(MountPlanReplacement)


# NOTE: Do NOT call register_auditlog_signals() here at module level!
# It will be called from apps.py ready() method after all models are loaded.
