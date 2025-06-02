from django.core.exceptions import ValidationError


def validate_layer_extra_feature_info(value):
    """Validator to check Layer model's extra_feature_info field.
    For each key there has to be title_fi in the payload dict.
    """
    if value:
        for k, v in value.items():
            if v is None:
                raise ValidationError(f"Extra Feature Info field data value cannot be empty for key: {k}")
            if "title_fi" not in list(v.keys()):
                raise ValidationError(f"Extra field {k} does not have mandatory value title_fi")
            if not all(v.values()):
                raise ValidationError(f"Extra Feature Info field data cannot be empty: {v}")
