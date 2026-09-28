from django.db import models
from gisserver.types import GeometryXsdElement, XsdElement, XsdTypes


class EnumNameXsdElement(XsdElement):
    def get_value(self, instance: models.Model):
        """Return the enum name as a string value.

        Args:
            instance: The Django model instance.

        Returns:
            str | None: The enum's name attribute (e.g., "RIGHT", "ACTIVE"), or None if field is empty.
        """
        if not (enum_value := getattr(instance, self.name)):
            return None
        return enum_value.name


class EnumIntegerNameXsdElement(EnumNameXsdElement):
    """XsdElement for EnumIntegerField that returns the enum's name as a string value.

    This is used for fields that are stored as integers in the database (EnumIntegerField)
    but should be exposed as string names in WFS responses. It overrides the type to
    XsdTypes.string to match the returned value format, preventing type mismatches in
    WFS clients like QGIS.

    The key difference from EnumNameXsdElement is that this explicitly declares the XSD
    type as string in the schema, whereas EnumNameXsdElement auto-detects based on the
    database field type (which works fine for EnumField but fails for EnumIntegerField).

    Examples:
        - location_specifier: stored as 1 (integer), returns "RIGHT" (string), schema declares string
        - lifecycle: stored as 3 (integer), returns "ACTIVE" (string), schema declares string
        - condition: stored as 1 (integer), returns "VERY_BAD" (string), schema declares string
        - color: stored as 1 (integer), returns "BLUE" (string), schema declares string
        - arrow_direction: stored as 1 (integer), returns "UP" (string), schema declares string
    """

    def __init__(self, name: str, **kwargs):
        """Initialize with type forced to XsdTypes.string.

        Args:
            name: The field name.
            **kwargs: Additional arguments passed to parent XsdElement.
        """
        # Force the type to be string, overriding any auto-detected type
        kwargs["type"] = XsdTypes.string
        super().__init__(name, **kwargs)


class CentroidLocationXsdElement(GeometryXsdElement):
    def get_value(self, instance: models.Model):
        return getattr(instance, "centroid_location", None)


class IconXsdElement(XsdElement):
    def get_value(self, instance: models.Model):
        # instance needs to have device_type field
        if instance.device_type and instance.device_type.icon_file:
            return instance.device_type.icon_name
        return None


class ContentSRowSElement(XsdElement):
    def get_value(self, instance: models.Model):
        # instance needs to have content_s_rows attribute
        if hasattr(instance, "content_s"):
            return instance.get_content_s_rows()
        return None


class RealCountXsdElement(XsdElement):
    """XsdElement exposing the number of reals that realize a device plan.

    The value is read from the ``real_count`` annotation that the feature type's queryset adds.
    The XSD type is forced to integer, because the element is bound to the model's ``id`` field
    as a workaround for django-gisserver requiring an actual model field.
    """

    def __init__(self, name: str, **kwargs):
        """Initialize with type forced to XsdTypes.integer.

        Args:
            name (str): The field name.
            **kwargs: Additional arguments passed to parent XsdElement.
        """
        kwargs["type"] = XsdTypes.integer
        super().__init__(name, **kwargs)

    def get_value(self, instance: models.Model) -> int:
        """Return the annotated count of reals for the given plan instance.

        Args:
            instance (models.Model): The device plan instance.

        Returns:
            int: Number of reals referencing this plan, 0 when the annotation is missing.
        """
        return getattr(instance, "real_count", 0)
