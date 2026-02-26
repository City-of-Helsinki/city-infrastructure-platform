import pytest
from django.urls import reverse

from city_furniture.tests.factories import FurnitureSignpostPlanFactory
from traffic_control.tests.factories import ResponsibleEntityFactory

# ------------------------------------------------------------------------------
# TreeModelFieldListFilter Tests
# ------------------------------------------------------------------------------


@pytest.mark.django_db
def test_furniture_signpost_plan_responsible_entity_filter_does_not_crash(admin_client):
    # 1. Create an entity and a plan so the filter has an active choice to evaluate
    entity = ResponsibleEntityFactory()
    FurnitureSignpostPlanFactory(responsible_entity=entity)

    # 2. Resolve the admin changelist URL
    url = reverse("admin:city_furniture_furnituresignpostplan_changelist")

    # 3. Define the query parameters to simulate clicking the filter option.
    query_params = {"responsible_entity__id__exact": entity.id}

    # 4. Perform the GET request.
    response = admin_client.get(url, query_params)

    # 5. Assert the page loads successfully.
    assert response.status_code == 200


@pytest.mark.django_db
def test_furniture_signpost_plan_responsible_entity_filter_results(admin_client):
    # 1. Create two distinct entities
    entity_target = ResponsibleEntityFactory()
    entity_other = ResponsibleEntityFactory()

    # 2. Create a plan for each entity
    plan_target = FurnitureSignpostPlanFactory(responsible_entity=entity_target)
    plan_other = FurnitureSignpostPlanFactory(responsible_entity=entity_other)

    # 3. Resolve the admin changelist URL
    url = reverse("admin:city_furniture_furnituresignpostplan_changelist")

    # 4. Filter specifically by the target entity
    query_params = {"responsible_entity__id__exact": entity_target.id}
    response = admin_client.get(url, query_params)

    # 5. Assert the page loads successfully
    assert response.status_code == 200

    # 6. Extract the evaluated results from the admin ChangeList
    result_list = response.context["cl"].result_list

    # 7. Verify the filtering logic works
    assert len(result_list) == 1
    assert plan_target in result_list
    assert plan_other not in result_list


@pytest.mark.django_db
def test_furniture_signpost_plan_responsible_entity_filter_hierarchy(admin_client):
    # 1. Create a tree hierarchy of entities: A -> (B, C)
    entity_a = ResponsibleEntityFactory()
    entity_b = ResponsibleEntityFactory(parent=entity_a)
    entity_c = ResponsibleEntityFactory(parent=entity_a)

    # 2. Create a plan assigned to each level of the tree
    plan_a = FurnitureSignpostPlanFactory(responsible_entity=entity_a)
    plan_b = FurnitureSignpostPlanFactory(responsible_entity=entity_b)
    plan_c = FurnitureSignpostPlanFactory(responsible_entity=entity_c)

    url = reverse("admin:city_furniture_furnituresignpostplan_changelist")

    # --- Scenario 1: Filter by the Parent Node (Entity A) ---
    # Expected: Should return Plan A, Plan B, and Plan C
    query_params_a = {"responsible_entity__id__exact": entity_a.id}
    response_a = admin_client.get(url, query_params_a)

    assert response_a.status_code == 200
    result_list_a = response_a.context["cl"].result_list

    assert len(result_list_a) == 3
    assert plan_a in result_list_a
    assert plan_b in result_list_a
    assert plan_c in result_list_a

    # --- Scenario 2: Filter by a Child Node (Entity B) ---
    # Expected: Should return ONLY Plan B (no ancestors, no siblings)
    query_params_b = {"responsible_entity__id__exact": entity_b.id}
    response_b = admin_client.get(url, query_params_b)

    assert response_b.status_code == 200
    result_list_b = response_b.context["cl"].result_list

    assert len(result_list_b) == 1
    assert plan_b in result_list_b
    assert plan_a not in result_list_b  # Fails if it includes ancestors
    assert plan_c not in result_list_b  # Fails if it includes siblings
