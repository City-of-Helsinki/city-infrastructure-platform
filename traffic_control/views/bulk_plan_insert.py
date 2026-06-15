import graphlib
from collections import defaultdict

from django.db import transaction
from rest_framework import serializers

from traffic_control.serializers.additional_sign import (
    AdditionalSignPlanInputSerializer,
    AdditionalSignPlanOutputSerializer,
)
from traffic_control.serializers.mount import MountPlanInputSerializer, MountPlanOutputSerializer
from traffic_control.serializers.plan import PlanSerializer
from traffic_control.serializers.signpost import SignpostPlanInputSerializer, SignpostPlanOutputSerializer
from traffic_control.serializers.traffic_sign import TrafficSignPlanInputSerializer, TrafficSignPlanOutputSerializer

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
    plans = BulkPlanInputSerializerPlanItem(many=True, required=True)
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
            for object_data in attrs.get(object_type, []):
                dependencies = []
                for dependency_field in DEPENDENCY_ID_FIELDS:
                    if dependency_field in object_data and object_data[dependency_field]:
                        dependencies.append(object_data[dependency_field])

                object_id = object_data["id"]
                self._object_type_and_data_map[object_id] = {"type": object_type, "data": object_data}
                sorter.add(object_id, *dependencies)

        try:
            self._object_topological_order = list(sorter.static_order())
        except graphlib.CycleError as e:
            raise serializers.ValidationError({"dependencies": f"Circular dependency detected: {e}"})

        return attrs

    # https://www.django-rest-framework.org/api-guide/serializers/#writing-create-methods-for-nested-representations
    def create(self, validated_data):
        """
        Sequential object creation in a transaction.

        Due to dependencies between objects being created, objects need to be created in topological order. The method
        may raise further validation errors if any objects fail creation along the way.
        """
        created_objects_by_type = defaultdict(list)
        created_objects_by_pk = {}

        errors = defaultdict(list)
        with transaction.atomic():
            for object_id in self._object_topological_order:
                try:
                    object_info = self._object_type_and_data_map[object_id]
                    object_type = object_info["type"]
                    object_data = object_info["data"]
                    object_serializer = self.fields[object_type].child

                    # NOTE (2026-06-25 thiago)
                    # Because django-rest-framework's object existence validation has been bypassed, we have to
                    # explicitly resolve the FK references into objects ourselves
                    for dependency_field in DEPENDENCY_ID_FIELDS:
                        if dependency_field in object_data and object_data[dependency_field]:
                            dependency_pk = object_data[dependency_field]
                            if dependency_pk not in created_objects_by_pk:
                                raise ValueError(f"Dependency {dependency_field} ({dependency_pk}) was not created.")
                            object_data[dependency_field] = created_objects_by_pk[dependency_pk]

                    instance = object_serializer.create(object_data)
                    created_objects_by_type[object_type].append(instance)
                    created_objects_by_pk[instance.pk] = instance
                except Exception as e:
                    errors[object_type].append({str(object_id): e})

            if errors:
                raise serializers.ValidationError(detail=errors)
        return created_objects_by_type


class BulkPlanInputResponseSerializer(serializers.Serializer):
    additional_sign_plans = AdditionalSignPlanOutputSerializer(many=True, required=False, default=list)
    mount_plans = MountPlanOutputSerializer(many=True, required=False, default=list)
    plans = PlanSerializer(many=True, required=True)
    signpost_plans = SignpostPlanOutputSerializer(many=True, required=False, default=list)
    traffic_sign_plans = TrafficSignPlanOutputSerializer(many=True, required=False, default=list)
