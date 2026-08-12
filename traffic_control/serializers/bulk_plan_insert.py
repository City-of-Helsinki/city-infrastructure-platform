import graphlib
from collections import defaultdict

from django.db import transaction
from rest_framework import serializers
from rest_framework.settings import api_settings

from traffic_control.serializers.additional_sign import (
    AdditionalSignPlanInputSerializer,
    AdditionalSignPlanOutputSerializer,
)
from traffic_control.serializers.mount import MountPlanInputSerializer, MountPlanOutputSerializer
from traffic_control.serializers.plan import PlanSerializer
from traffic_control.serializers.signpost import SignpostPlanInputSerializer, SignpostPlanOutputSerializer
from traffic_control.serializers.traffic_sign import TrafficSignPlanInputSerializer, TrafficSignPlanOutputSerializer
from traffic_control.serializers.utils import get_single_object_serializer

BULK_PLAN_INSERT_MOCK_BATCH_PAYLOAD = {
    "additional_sign_plans": [
        {
            "id": "44444444-4444-4444-4444-444444444444",
            "additional_information": "Example additional sign for v1/plans/bulk-insert operation",
            "device_type": "b8a75edb-bd54-4c00-b3b2-ec3b16719dea",
            "location": "SRID=3879;POINT Z (25496751.5 6673129.5 1.5)",
            "missing_content": False,
            "mount_plan": "11111111-1111-1111-1111-111111111111",
            "owner": "3e067c4d-ac36-4160-b5d4-a19fc2b346d4",
            "parent": "33333333-3333-3333-3333-333333333333",
            "plan": "00000000-0000-0000-0000-000000000000",
            "seasonal_validity_period_information": "",
        }
    ],
    "mount_plans": [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "location": (
                "SRID=3879;MULTIPOLYGON Z (((25497733.5 6672927.5 0, 25497946.5 6673032.5 0, 25498653.5 6673034.5 0, "
                "25498987.5 6672708.5 0, 25498314.5 6672170.5 0, 25497651.5 6672629.5 0, 25497646.5 6672775.5 0, "
                "25497733.5 6672927.5 0)))"
            ),
            "lifecycle": 3,
            "base": "Concrete",
            "txt": "Example mount plan for v1/plans/bulk-insert operation",
            "owner": "3e067c4d-ac36-4160-b5d4-a19fc2b346d4",
            "plan": "00000000-0000-0000-0000-000000000000",
        }
    ],
    "plans": [
        {
            "id": "00000000-0000-0000-0000-000000000000",
            "name": "Example plan for v1/plans/bulk-insert operation",
            "decision_id": "DEC-2026",
            "drawing_numbers": [],
            "derive_location": True,
        }
    ],
    "signpost_plans": [
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "device_type": "a7531a0f-c69f-447a-9146-f9c8effff985",
            "mount_plan": "11111111-1111-1111-1111-111111111111",
            "owner": "e757bb2d-4f93-41a8-96f9-2092c69bbb0e",
            "plan": "00000000-0000-0000-0000-000000000000",
            "double_sided": True,
            "lifecycle": 3,
            "location": "SRID=3879;POINT Z (25496751.5 6673129.5 1.5)",
            "parent": True,
            "replaces": True,
            "seasonal_validity_period_information": "",
            "txt": "Example signpost plan for v1/plans/bulk-insert operation",
        }
    ],
    "traffic_sign_plans": [
        {
            "id": "33333333-3333-3333-3333-333333333333",
            "device_type": "3a286199-ac5a-4249-bd9e-6ddd3365e1f9",
            "double_sided": True,
            "lifecycle": 3,
            "location": "SRID=3879;POINT Z (25496751.5 6673129.5 1.5)",
            "mount_plan": "11111111-1111-1111-1111-111111111111",
            "owner": "3e067c4d-ac36-4160-b5d4-a19fc2b346d4",
            "peak_fastened": True,
            "plan": "00000000-0000-0000-0000-000000000000",
            "seasonal_validity_period_information": "Winter constraints apply",
            "txt": "Example traffic sign plan for v1/plans/bulk-insert operation",
        }
    ],
}


# NOTE (2026-06-25 thiago)
# The serializers below override regular object input serializers with the following behavior changes:
# * require that the client provides a brand new UUID for the newly created object
# * recast foreign key relations for objects being built into UUID instead of references to specific models. This is
#   done to bypass the django-rest-framework's existence checks for the objects that haven't yet been added to the
#   database.


class BulkPlanInputSerializerAdditionalSignPlanItem(AdditionalSignPlanInputSerializer):
    id = serializers.UUIDField(required=True)
    plan = serializers.UUIDField(required=True)
    mount_plan = serializers.UUIDField(required=False, allow_null=True)
    parent = serializers.UUIDField(required=False, allow_null=True)
    signpost_plan = serializers.UUIDField(required=False, allow_null=True)


class BulkPlanInputSerializerMountPlanItem(MountPlanInputSerializer):
    id = serializers.UUIDField(required=True)
    plan = serializers.UUIDField(required=True)


class BulkPlanInputSerializerPlanItem(PlanSerializer):
    id = serializers.UUIDField(required=True)


class BulkPlanInputSerializerSignpostPlanItem(SignpostPlanInputSerializer):
    id = serializers.UUIDField(required=True)
    plan = serializers.UUIDField(required=True)
    mount_plan = serializers.UUIDField(required=False, allow_null=True)
    parent = serializers.UUIDField(required=False, allow_null=True)


class BulkPlanInputSerializerTrafficSignPlanItem(TrafficSignPlanInputSerializer):
    id = serializers.UUIDField(required=True)
    plan = serializers.UUIDField(required=True)
    mount_plan = serializers.UUIDField(required=False, allow_null=True)


DEPENDENCY_ID_FIELDS = {"plan", "mount_plan", "parent", "signpost_plan"}


class BulkPlanInputSerializer(serializers.Serializer):
    additional_sign_plans = BulkPlanInputSerializerAdditionalSignPlanItem(many=True, required=False, default=list)
    mount_plans = BulkPlanInputSerializerMountPlanItem(many=True, required=False, default=list)
    plan = BulkPlanInputSerializerPlanItem(many=False, required=True)
    signpost_plans = BulkPlanInputSerializerSignpostPlanItem(many=True, required=False, default=list)
    traffic_sign_plans = BulkPlanInputSerializerTrafficSignPlanItem(many=True, required=False, default=list)

    def __init__(self, instance=None, data=None, **kwargs):
        super().__init__(instance, data, **kwargs)
        self._object_type_and_data_map = {}
        self._object_topological_order = []

    # https://www.django-rest-framework.org/api-guide/serializers/#object-level-validation
    def validate(self, attrs):
        """
        Custom validation to detect dependency cycles between the objects being created.

        Some models have ForeignKey fields to "self" so this check is necessary. Also take the opportunity to resolve a
        build order for the incoming objects that will satisfy their interdependencies.
        """
        # Build dependency graph and object type/data map
        sorter = graphlib.TopologicalSorter()
        for object_type in self.fields:
            # Cast single-entry fields to arrays for uniform processing
            entries_data = _to_list(attrs.get(object_type, []))

            for index, object_data in enumerate(entries_data):
                dependencies = [object_data[field] for field in DEPENDENCY_ID_FIELDS if object_data.get(field)]

                object_id = object_data["id"]
                self._object_type_and_data_map[object_id] = {
                    "type": object_type,
                    "data": object_data,
                    "index": index,
                }
                sorter.add(object_id, *dependencies)

        try:
            self._object_topological_order = list(sorter.static_order())
        except graphlib.CycleError as e:
            error_msg = e.args[0]
            error_nodes = ", ".join([str(node) for node in e.args[1]])
            raise serializers.ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [f"{error_msg}: {error_nodes}"]})

        return attrs

    # https://www.django-rest-framework.org/api-guide/serializers/#writing-create-methods-for-nested-representations
    def create(self, validated_data):
        """
        Sequential object creation in a transaction.

        Due to dependencies between objects being created, objects need to be created in topological order. The method
        may raise further validation errors if any objects fail creation along the way.
        """
        created_objects_by_pk = {}
        errors = self._stub_errors_map(validated_data)
        # Treat all fields as lists to simplify method logic
        created_objects_by_type = defaultdict(list)

        with transaction.atomic():
            for object_id in self._object_topological_order:
                object_info = self._object_type_and_data_map[object_id]
                object_type = object_info["type"]
                object_data = object_info["data"]
                object_index = object_info["index"]
                object_serializer = get_single_object_serializer(self.fields[object_type])

                try:
                    instance = self._create_serialize_object(
                        object_serializer=object_serializer,
                        object_data=object_data,
                        created_objects_by_pk=created_objects_by_pk,
                    )
                    created_objects_by_type[object_type].append(instance)
                    created_objects_by_pk[instance.pk] = instance
                except Exception as e:
                    # Allow errors to pile up for a comprehensive error response
                    error_detail = (
                        e.detail
                        if isinstance(e, serializers.ValidationError)
                        else {api_settings.NON_FIELD_ERRORS_KEY: [str(e)]}
                    )
                    errors[object_type][object_index] = error_detail

            # Check if we have errors and return them if any, reshaping error map to conform to input data structure
            cleaned_errors = self._reshape_and_filter_errors_map(errors)
            if cleaned_errors:
                raise serializers.ValidationError(detail=cleaned_errors)

        # Return our objects-by-type structure after reshaping it to conform to input data structure
        return self._reshape_created_objects_by_type(created_objects_by_type)

    def _create_serialize_object(
        self, *, object_serializer: serializers.ModelSerializer, object_data: dict, created_objects_by_pk: dict
    ):
        """Resolve dependency fields for a given object and instance the object."""
        # NOTE (2026-06-25 thiago)
        # Because django-rest-framework's object existence validation has been bypassed, we have to explicitly resolve
        # the FK references into objects ourselves
        for dependency_field in DEPENDENCY_ID_FIELDS:
            if dependency_field in object_data and object_data[dependency_field]:
                dependency_pk = object_data[dependency_field]
                if dependency_pk not in created_objects_by_pk:
                    raise serializers.ValidationError(
                        {
                            dependency_field: [
                                f"Dependency {dependency_field} ({dependency_pk}) was not created by " "this request."
                            ]
                        }
                    )
                object_data[dependency_field] = created_objects_by_pk[dependency_pk]

        return object_serializer.create(object_data)

    def _stub_errors_map(self, validated_data):
        """Pre-allocate DRF-style error lists. Single-value fields are also treated as lists."""
        errors = {}
        for field_name in self.fields:
            if field_name in validated_data:
                entries = _to_list(validated_data[field_name])
                errors[field_name] = [{} for _ in range(len(entries))]
        return errors

    def _reshape_and_filter_errors_map(self, errors):
        """Reshape the errors-by-field dict to fit the serializer's input format. Filter out fields with no errors."""
        cleaned_errors = {}
        for field_name, errors_list in errors.items():
            if any(errors_list):
                if isinstance(self.fields[field_name], serializers.ListSerializer):
                    cleaned_errors[field_name] = errors_list
                else:
                    cleaned_errors[field_name] = errors_list[0]

        return cleaned_errors

    def _reshape_created_objects_by_type(self, created_objects_by_type):
        """Reshape the objects-by-type dict to fit the serializer's input format."""
        result = {}
        for field_name, field_value in created_objects_by_type.items():
            if isinstance(self.fields[field_name], serializers.ListSerializer):
                result[field_name] = field_value
            else:
                result[field_name] = field_value[0]
        return result


class BulkPlanInputResponseSerializer(serializers.Serializer):
    additional_sign_plans = AdditionalSignPlanOutputSerializer(many=True, required=False, default=list)
    mount_plans = MountPlanOutputSerializer(many=True, required=False, default=list)
    plan = PlanSerializer(many=False, required=True)
    signpost_plans = SignpostPlanOutputSerializer(many=True, required=False, default=list)
    traffic_sign_plans = TrafficSignPlanOutputSerializer(many=True, required=False, default=list)


def _to_list(value) -> list:
    """Cast the value as a list."""
    if isinstance(value, list):
        return value
    else:
        return [value]
