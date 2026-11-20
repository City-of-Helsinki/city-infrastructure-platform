"""Tests for accepting ``null`` input on optional string fields and storing it as ``""``."""

from typing import Iterator

import pytest
from django.db import models
from django.urls import reverse
from rest_framework import serializers, status
from rest_framework.routers import BaseRouter

from cityinfra import urls as root_urls
from traffic_control.models import Plan, SignpostMigrationRealRecord, TrafficControlDeviceType, TrafficSignReal
from traffic_control.serializers import bulk_plan_insert
from traffic_control.serializers.common import (
    accepts_null_as_empty_string,
    NullToEmptyStringFieldMixin,
    NullToEmptyStringSerializerMixin,
)
from traffic_control.tests.factories import get_api_client, get_user, PlanFactory, TrafficSignRealFactory


class DeviceTypeSerializer(NullToEmptyStringSerializerMixin, serializers.ModelSerializer):
    """Serializer with a required string, an optional string and an enum field."""

    class Meta:
        model = TrafficControlDeviceType
        fields = ("code", "unit", "target_model")


class TrafficSignRealTextSerializer(NullToEmptyStringSerializerMixin, serializers.ModelSerializer):
    """Serializer with an optional TextField, a string field that stays nullable and an enum field."""

    class Meta:
        model = TrafficSignReal
        fields = ("seasonal_validity_period_information", "source_name", "size")
        extra_kwargs = {"source_name": {"required": False}}


class MigrationRecordSerializer(NullToEmptyStringSerializerMixin, serializers.ModelSerializer):
    """Serializer with an optional URLField and a read-only optional string field."""

    class Meta:
        model = SignpostMigrationRealRecord
        fields = ("lost_attachment_url", "lost_rfid")
        read_only_fields = ("lost_rfid",)


@pytest.mark.parametrize(
    "value, expected",
    ((None, ""), ("", ""), ("m", "m")),
    ids=("null_becomes_empty_string", "empty_string_kept", "value_kept"),
)
@pytest.mark.django_db
def test__optional_char_field__input_is_normalized(value: str | None, expected: str) -> None:
    """null becomes "", and "" and real values pass through unchanged."""
    serializer = DeviceTypeSerializer(data={"code": "X1", "unit": value})

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["unit"] == expected


def test__optional_text_field__null_becomes_empty_string() -> None:
    """TextFields are covered as well as CharFields."""
    serializer = TrafficSignRealTextSerializer(data={"seasonal_validity_period_information": None}, partial=True)

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["seasonal_validity_period_information"] == ""


def test__nullable_string_field__null_is_kept() -> None:
    """Fields that stay nullable in the model must keep storing null."""
    serializer = TrafficSignRealTextSerializer(data={"source_name": None}, partial=True)

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["source_name"] is None
    assert not isinstance(serializer.fields["source_name"], NullToEmptyStringFieldMixin)


@pytest.mark.django_db
def test__required_string_field__null_is_still_rejected() -> None:
    """The tolerance is for optional fields only."""
    serializer = DeviceTypeSerializer(data={"code": None, "unit": "m"})

    assert not serializer.is_valid()
    assert serializer.errors["code"][0].code == "null"


@pytest.mark.django_db
def test__partial_update__omitted_field_is_not_touched() -> None:
    """A field that is absent from a PATCH must not be overwritten with ""."""
    serializer = DeviceTypeSerializer(data={"code": "X1"}, partial=True)

    assert serializer.is_valid(), serializer.errors
    assert "unit" not in serializer.validated_data


@pytest.mark.parametrize("field_name", ("target_model", "size"))
def test__enum_fields__are_not_wrapped(field_name: str) -> None:
    """Enum fields store "no value" as null and must keep doing so."""
    serializer_class = DeviceTypeSerializer if field_name == "target_model" else TrafficSignRealTextSerializer

    assert not isinstance(serializer_class().fields[field_name], NullToEmptyStringFieldMixin)


@pytest.mark.parametrize(
    "model_field, expected",
    (
        (models.CharField(max_length=10, blank=True), True),
        (models.TextField(blank=True), True),
        (models.URLField(blank=True), True),
        (models.CharField(max_length=10, blank=True, null=True), False),
        (models.CharField(max_length=10), False),
        (models.CharField(max_length=10, blank=True, choices=[("a", "A")]), False),
        (models.IntegerField(blank=True), False),
    ),
    ids=("char", "text", "url", "nullable", "required", "choices", "non_string"),
)
def test__accepts_null_as_empty_string(model_field: models.Field, expected: bool) -> None:
    """The predicate picks optional, non-nullable string fields without choices, and nothing else."""
    assert accepts_null_as_empty_string(model_field) is expected


def test__url_field__null_becomes_empty_string_and_url_validation_is_kept() -> None:
    """Swapping the field class must not lose the URL validation."""
    field = MigrationRecordSerializer().fields["lost_attachment_url"]
    assert isinstance(field, serializers.URLField)
    assert isinstance(field, NullToEmptyStringFieldMixin)

    valid = MigrationRecordSerializer(data={"lost_attachment_url": None})
    assert valid.is_valid(), valid.errors
    assert valid.validated_data["lost_attachment_url"] == ""

    invalid = MigrationRecordSerializer(data={"lost_attachment_url": "not a url"})
    assert not invalid.is_valid()
    assert "lost_attachment_url" in invalid.errors


def test__read_only_field__input_is_ignored() -> None:
    """Read-only fields take no input, null included."""
    serializer = MigrationRecordSerializer(data={"lost_rfid": None})

    assert serializer.is_valid(), serializer.errors
    assert "lost_rfid" not in serializer.validated_data


def _api_serializer_classes() -> Iterator[type[serializers.Serializer]]:
    """Yield every serializer class reachable from the registered API viewsets and bulk plan insert.

    Yields:
        type[serializers.Serializer]: Serializer classes used by the API.
    """
    routers = [obj for obj in vars(root_urls).values() if isinstance(obj, BaseRouter)]
    for router in routers:
        for _prefix, viewset, _basename in router.registry:
            yield from getattr(viewset, "serializer_classes", {}).values()
            if getattr(viewset, "serializer_class", None):
                yield viewset.serializer_class
    for item in vars(bulk_plan_insert).values():
        if isinstance(item, type) and issubclass(item, serializers.ModelSerializer):
            yield item


def _model_field(serializer_class: type[serializers.ModelSerializer], field: serializers.Field) -> models.Field | None:
    """Return the model field a serializer field writes to, or None for non-model fields.

    Args:
        serializer_class (type[serializers.ModelSerializer]): Serializer the field belongs to.
        field (serializers.Field): Bound serializer field.

    Returns:
        models.Field | None: The concrete model field, if the field maps to one directly.
    """
    try:
        return serializer_class.Meta.model._meta.get_field(field.source)
    except Exception:
        return None


def _optional_string_fields(
    serializer: serializers.BaseSerializer, path: str
) -> Iterator[tuple[str, serializers.Field]]:
    """Yield writable optional string fields of a serializer, descending into nested serializers.

    Args:
        serializer (serializers.BaseSerializer): Serializer (or list serializer) to walk.
        path (str): Dotted path of the serializer, used in failure messages.

    Yields:
        tuple[str, serializers.Field]: Dotted field path and the bound field.
    """
    if isinstance(serializer, serializers.ListSerializer):
        serializer = serializer.child
    if not isinstance(serializer, serializers.ModelSerializer):
        return
    for name, field in serializer.fields.items():
        if field.read_only:
            continue
        if isinstance(field, serializers.BaseSerializer):
            yield from _optional_string_fields(field, f"{path}.{name}")
            continue
        model_field = _model_field(type(serializer), field)
        if model_field is not None and accepts_null_as_empty_string(model_field):
            yield f"{path}.{name}", field


def test__all_api_serializers__accept_null_for_optional_string_fields() -> None:
    """Guard: every writable optional string field in the API must accept null, also on the GeoJSON write path."""
    checked = 0
    missing = []
    for serializer_class in set(_api_serializer_classes()):
        root_path = f"{serializer_class.__module__}.{serializer_class.__name__}"
        for path, field in _optional_string_fields(serializer_class(), root_path):
            checked += 1
            if not isinstance(field, NullToEmptyStringFieldMixin):
                missing.append(path)

    assert checked > 0
    assert missing == []


def test__guard__descends_into_nested_serializers() -> None:
    """The guard below would miss nested serializers if it only looked at top-level fields."""

    class NestedSerializer(serializers.ModelSerializer):
        """Nested serializer that lacks the mixin."""

        class Meta:
            model = TrafficControlDeviceType
            fields = ("unit",)

    class ParentSerializer(NullToEmptyStringSerializerMixin, serializers.ModelSerializer):
        """Serializer with the mixin and a nested serializer without it."""

        nested = NestedSerializer(many=True)

        class Meta:
            model = TrafficSignReal
            fields = ("seasonal_validity_period_information", "nested")

    paths = {path: field for path, field in _optional_string_fields(ParentSerializer(), "Parent")}

    assert set(paths) == {"Parent.seasonal_validity_period_information", "Parent.nested.unit"}
    assert not isinstance(paths["Parent.nested.unit"], NullToEmptyStringFieldMixin)


@pytest.mark.django_db
@pytest.mark.parametrize("geo_format", ("", "geojson"))
@pytest.mark.parametrize(
    "field_name, old_value",
    (
        ("seasonal_validity_period_information", "Summer only"),
        ("txt", "Old text"),
        ("attachment_url", "https://example.com/old"),
    ),
)
def test__api_patch__null_for_optional_string_field_is_stored_as_empty_string(
    field_name: str, old_value: str, geo_format: str
) -> None:
    """End to end through the API, in both response formats: null is accepted and "" is stored and returned."""
    client = get_api_client(user=get_user(admin=True))
    sign = TrafficSignRealFactory(**{field_name: old_value})
    url = reverse("v1:trafficsignreal-detail", kwargs={"pk": sign.pk})

    response = client.patch(f"{url}?geo_format={geo_format}", data={field_name: None})

    assert response.status_code == status.HTTP_200_OK, response.json()
    sign.refresh_from_db()
    assert getattr(sign, field_name) == ""
    assert response.json()[field_name] == ""


@pytest.mark.django_db
def test__api_create__null_for_optional_string_fields_is_stored_as_empty_string() -> None:
    """End to end on create: null is accepted and "" is stored and returned."""
    client = get_api_client(user=get_user(admin=True))
    plan = PlanFactory()
    data = {"name": "Plan with nulls", "decision_id": "2026-1", "decision_url": None, "location": str(plan.location)}

    response = client.post(reverse("v1:plan-list"), data=data)

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert response.json()["decision_url"] == ""
    assert Plan.objects.get(pk=response.json()["id"]).decision_url == ""
