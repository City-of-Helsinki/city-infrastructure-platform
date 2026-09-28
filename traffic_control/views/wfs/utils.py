from typing import Optional
from uuid import UUID

from django.db import models
from gisserver.features import FeatureType
from gisserver.projection import FeatureRelation
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
    """XsdElement exposing the file name of the device type's icon.

    The element is bound to the ``device_type.icon_file`` relation so that django-gisserver
    includes it in the projection and resolves it with the main query. Binding it to a local field
    instead would leave the relation deferred and cause two extra queries per rendered feature.

    The XSD type is forced to string, because the bound model attribute is a foreign key while the
    rendered value is the icon's file name.
    """

    def __init__(self, name: str, **kwargs):
        """Initialize with type forced to XsdTypes.string.

        Args:
            name (str): The field name.
            **kwargs: Additional arguments passed to parent XsdElement.
        """
        kwargs["type"] = XsdTypes.string
        super().__init__(name, **kwargs)

    def get_value(self, instance: models.Model) -> Optional[str]:
        """Return the icon file name of the instance's device type.

        Args:
            instance (models.Model): The device instance, which must have a ``device_type``.

        Returns:
            Optional[str]: The icon's file name, or None when there is no icon.
        """
        if instance.device_type and instance.device_type.icon_file:
            return instance.device_type.icon_name
        return None


class ContentSRowSElement(XsdElement):
    """XsdElement exposing the structured content rows of an additional sign.

    The element is bound to ``device_type.content_schema`` so that django-gisserver includes
    that column in the queryset projection. Without it, ``get_content_s_rows()`` would read a
    deferred field and issue one query per rendered feature.
    """

    def __init__(self, name: str, **kwargs):
        """Initialize with the published type and nillability of the original ``id`` binding.

        Args:
            name (str): The field name.
            **kwargs: Additional arguments passed to parent XsdElement.
        """
        kwargs["type"] = XsdTypes.anyType
        kwargs["nillable"] = False
        super().__init__(name, **kwargs)

    def get_value(self, instance: models.Model):
        """Return the structured content rows of the additional sign.

        Args:
            instance (models.Model): The additional sign instance being rendered.

        Returns:
            list | None: The content rows in priority order, or None when unavailable.
        """
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


class AnnotatedIdXsdElement(XsdElement):
    """XsdElement exposing an ID that the feature type's queryset provides as an annotation.

    The annotation is expected to be named ``wfs_<element name>``. Resolving these IDs with a
    queryset annotation keeps them part of the main query, whereas binding the element to an ORM
    relation makes django-gisserver emit a separate prefetch with one ID per rendered feature.
    """

    def __init__(self, name: str, **kwargs):
        """Initialize with nillability forced on, as an annotated ID can be absent.

        Args:
            name (str): The field name.
            **kwargs: Additional arguments passed to parent XsdElement.
        """
        kwargs["nillable"] = True
        super().__init__(name, **kwargs)

    def get_value(self, instance: models.Model) -> Optional[UUID]:
        """Return the annotated ID for the given instance.

        Args:
            instance (models.Model): The device instance being rendered.

        Returns:
            Optional[UUID]: The annotated ID, or None when there is none.
        """
        return getattr(instance, f"wfs_{self.name}", None)


class FullRelationFeatureType(FeatureType):
    """FeatureType that prefetches complete related objects.

    django-gisserver limits prefetched related objects to the columns that the feature type
    publishes. Model code that runs while rendering - most notably ``__str__()``, which provides
    the ``gml:name`` / GeoJSON display value - may read other columns, which then triggers a
    deferred field load per object. The related models used here are small lookup tables, so
    fetching them in full is cheaper than the resulting N+1 queries.
    """

    def get_related_queryset(self, feature_relation: FeatureRelation) -> models.QuerySet:
        """Return an unrestricted queryset for prefetching a related model.

        Args:
            feature_relation (FeatureRelation): The relation that is being prefetched.

        Returns:
            models.QuerySet: Queryset returning complete instances of the related model.

        Raises:
            RuntimeError: If the related model of the relation is not known.
        """
        if feature_relation.related_model is None:
            raise RuntimeError(
                f"Unable to create prefetch queryset for relation {feature_relation.orm_path}, "
                f"source model is not defined for: {feature_relation.xsd_elements!r}"
            )
        return self.filter_related_queryset(feature_relation.related_model.objects.all())
