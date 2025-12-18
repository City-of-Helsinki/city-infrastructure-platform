"""
Shared utilities for device_type migrations and management commands.
This module contains common logic for creating dummy device types and
updating null device_type values, used by both migrations and management commands.
"""


def get_traffic_control_models_with_device_type():
    """
    Return list of model names that have device_type field in traffic_control app.
    Used by both migrations and management commands.
    """
    return [
        "AdditionalSignPlan",
        "AdditionalSignReal",
        "BarrierPlan",
        "BarrierReal",
        "RoadMarkingPlan",
        "RoadMarkingReal",
        "SignpostPlan",
        "SignpostReal",
        "TrafficLightPlan",
        "TrafficLightReal",
        "TrafficSignPlan",
        "TrafficSignReal",
    ]


def set_dummy_device_type_for_null_values(
    apps,
    schema_editor,
    app_label="traffic_control",
    device_type_model_name="TrafficControlDeviceType",
    model_names=None,
):
    """
    Create or get the DummyDT device type and set it for all devices with null device_type.

    This is the core logic shared between migrations and management commands.

    Args:
        apps: Django apps registry (for migrations) or None (for management commands)
        schema_editor: Schema editor (for migrations) or None
        app_label: App label ('traffic_control' or 'city_furniture')
        device_type_model_name: Name of the device type model
        model_names: List of model names to update, or None for default list

    Returns:
        tuple: (dummy_device_type, total_updated)
    """
    if model_names is None:
        if app_label == "traffic_control":
            model_names = get_traffic_control_models_with_device_type()
        elif app_label == "city_furniture":
            from city_furniture.utils.device_type_migration import get_city_furniture_models_with_device_type
            model_names = get_city_furniture_models_with_device_type()
        else:
            raise ValueError(f"Unknown app_label: {app_label}")

    # Get the device type model
    DeviceTypeModel = apps.get_model(app_label, device_type_model_name)

    # Get or create the DummyDT device type
    dummy_dt, created = DeviceTypeModel.objects.get_or_create(
        code="DummyDT",
        defaults={
            "description": "Placeholder for devices that have None set to device_type",
            "target_model": None,
        },
    )

    if created:
        print(f"Created dummy device type: DummyDT")

    # Update models with null device_type
    total_updated = 0
    for model_name in model_names:
        try:
            Model = apps.get_model(app_label, model_name)
            updated = Model.objects.filter(device_type__isnull=True).update(device_type=dummy_dt)
            if updated > 0:
                print(f"  Updated {updated} {model_name} records with DummyDT device type")
                total_updated += updated
        except LookupError:
            # Model doesn't exist, skip it
            pass

    if total_updated > 0:
        print(f"Total: Updated {total_updated} device records with DummyDT device type")
    else:
        print("No devices with device_type=None found")

    return dummy_dt, total_updated


def reverse_dummy_device_type(
    apps,
    schema_editor,
    app_label="traffic_control",
    device_type_model_name="TrafficControlDeviceType",
    model_names=None,
):
    """
    Reverse operation: set device_type back to null for all devices using DummyDT.

    Args:
        apps: Django apps registry (for migrations)
        schema_editor: Schema editor (for migrations)
        app_label: App label ('traffic_control' or 'city_furniture')
        device_type_model_name: Name of the device type model
        model_names: List of model names to reverse, or None for default list

    Returns:
        int: Total number of records reversed
    """
    if model_names is None:
        if app_label == "traffic_control":
            model_names = get_traffic_control_models_with_device_type()
        elif app_label == "city_furniture":
            from city_furniture.utils.device_type_migration import get_city_furniture_models_with_device_type
            model_names = get_city_furniture_models_with_device_type()
        else:
            raise ValueError(f"Unknown app_label: {app_label}")

    DeviceTypeModel = apps.get_model(app_label, device_type_model_name)

    try:
        dummy_dt = DeviceTypeModel.objects.get(code="DummyDT")
    except DeviceTypeModel.DoesNotExist:
        print("DummyDT device type not found, nothing to reverse")
        return 0

    total_updated = 0
    for model_name in model_names:
        try:
            Model = apps.get_model(app_label, model_name)
            updated = Model.objects.filter(device_type=dummy_dt).update(device_type=None)
            if updated > 0:
                print(f"  Reversed {updated} {model_name} records back to null device_type")
                total_updated += updated
        except LookupError:
            pass

    if total_updated > 0:
        print(f"Total: Reversed {total_updated} device records back to null device_type")

    return total_updated

