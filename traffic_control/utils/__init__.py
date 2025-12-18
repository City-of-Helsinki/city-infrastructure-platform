"""
Traffic control utilities package.

This package contains utility functions and helpers for the traffic_control app.
"""

# Import and re-export all functions from common module for backward compatibility
from traffic_control.utils.common import (
    get_allowed_file_upload_types,
    get_client_ip,
    get_default_owner,
    get_file_upload_obstacles,
    get_icon_upload_obstacles,
    get_illegal_file_types,
    get_illegal_icon_file_types,
)

# Import device type migration utilities (used by migrations and management commands)
from traffic_control.utils.device_type_migration import (
    get_traffic_control_models_with_device_type,
    reverse_dummy_device_type,
    set_dummy_device_type_for_null_values,
)

__all__ = [
    # Common utilities
    "get_allowed_file_upload_types",
    "get_client_ip",
    "get_default_owner",
    "get_file_upload_obstacles",
    "get_icon_upload_obstacles",
    "get_illegal_file_types",
    "get_illegal_icon_file_types",
    # Device type migration utilities
    "get_traffic_control_models_with_device_type",
    "reverse_dummy_device_type",
    "set_dummy_device_type_for_null_values",
]

