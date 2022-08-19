from typing import List, Optional

import jsonschema
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from traffic_control.models.common import TrafficControlDeviceType


def validate_structured_content(content, device_type: Optional[TrafficControlDeviceType]) -> List[ValidationError]:
    validation_errors = []

    if device_type is not None:
        schema = device_type.content_schema
    else:
        schema = None

    if schema is not None:
        validator = jsonschema.Draft202012Validator(schema)

        for error in validator.iter_errors(content):
            message = error.message
            if error.path:
                # Add property path to the message
                message = ".".join(error.path) + ": " + message
            validation_errors.append(
                ValidationError(
                    message,
                    code="invalid_content_s",
                )
            )
    elif content is not None:
        validation_errors.append(
            ValidationError(
                _("Device type '%(device_type)s' accepts no structured content"),
                params={"device_type": str(device_type)},
                code="invalid_content_s",
            )
        )

    return validation_errors
