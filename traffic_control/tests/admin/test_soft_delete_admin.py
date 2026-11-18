"""Tests for the admin "Mark selected objects as deleted" action (SoftDeleteAdminMixin).

The action is exercised through the changelist POST, the same way the browser does it, so that
action registration, permission checks, audit logging and the model level cascades are all covered.
"""
from typing import Any

import pytest
from auditlog.models import LogEntry
from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.http import HttpResponse
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from factory.django import DjangoModelFactory

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.tests.factories import FurnitureSignpostPlanFactory, FurnitureSignpostRealFactory
from traffic_control.mixins.admin import SoftDeleteAdminMixin
from traffic_control.mixins.models import SoftDeleteModel
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    BarrierPlan,
    BarrierReal,
    MountPlan,
    MountReal,
    Plan,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    BarrierPlanFactory,
    BarrierRealFactory,
    MountPlanFactory,
    MountRealFactory,
    PlanFactory,
    ResponsibleEntityFactory,
    RoadMarkingPlanFactory,
    RoadMarkingRealFactory,
    SignpostPlanFactory,
    SignpostRealFactory,
    TrafficLightPlanFactory,
    TrafficLightRealFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
    UserFactory,
)
from users.models import User

FactoryClass = type[DjangoModelFactory]

SOFT_DELETE_ACTION = "action_soft_delete"

# Every model whose admin offers the soft delete action, with a factory that creates a valid instance.
# test_every_soft_delete_admin_is_covered fails when a new soft deletable admin is missing from here.
SOFT_DELETE_FACTORIES: dict[type[Model], FactoryClass] = {
    AdditionalSignPlan: AdditionalSignPlanFactory,
    AdditionalSignReal: AdditionalSignRealFactory,
    BarrierPlan: BarrierPlanFactory,
    BarrierReal: BarrierRealFactory,
    FurnitureSignpostPlan: FurnitureSignpostPlanFactory,
    FurnitureSignpostReal: FurnitureSignpostRealFactory,
    MountPlan: MountPlanFactory,
    MountReal: MountRealFactory,
    Plan: PlanFactory,
    RoadMarkingPlan: RoadMarkingPlanFactory,
    RoadMarkingReal: RoadMarkingRealFactory,
    SignpostPlan: SignpostPlanFactory,
    SignpostReal: SignpostRealFactory,
    TrafficLightPlan: TrafficLightPlanFactory,
    TrafficLightReal: TrafficLightRealFactory,
    TrafficSignPlan: TrafficSignPlanFactory,
    TrafficSignReal: TrafficSignRealFactory,
}

ALL_MODELS = pytest.mark.parametrize(
    "factory",
    [pytest.param(factory, id=model.__name__) for model, factory in SOFT_DELETE_FACTORIES.items()],
)

# (parent factory, child factory, name of the child's foreign key to the parent)
# Soft deleting the parent is expected to soft delete the active children too.
CASCADE_CASES = [
    pytest.param(TrafficSignPlanFactory, AdditionalSignPlanFactory, "parent", id="TrafficSignPlan"),
    pytest.param(TrafficSignRealFactory, AdditionalSignRealFactory, "parent", id="TrafficSignReal"),
    pytest.param(SignpostPlanFactory, AdditionalSignPlanFactory, "signpost_plan", id="SignpostPlan"),
    pytest.param(SignpostRealFactory, AdditionalSignRealFactory, "signpost_real", id="SignpostReal"),
]

# (parent factory, related factory, name of the related object's foreign key to the parent)
# Relations that soft delete does NOT follow today, asserted so that changing one is a deliberate decision.
# Not an exhaustive list of such relations.
NO_CASCADE_CASES = [
    pytest.param(PlanFactory, BarrierPlanFactory, "plan", id="Plan->BarrierPlan"),
    pytest.param(PlanFactory, TrafficSignPlanFactory, "plan", id="Plan->TrafficSignPlan"),
    pytest.param(MountPlanFactory, TrafficSignPlanFactory, "mount_plan", id="MountPlan->TrafficSignPlan"),
    pytest.param(MountRealFactory, TrafficSignRealFactory, "mount_real", id="MountReal->TrafficSignReal"),
    pytest.param(MountPlanFactory, AdditionalSignPlanFactory, "mount_plan", id="MountPlan->AdditionalSignPlan"),
    pytest.param(MountRealFactory, AdditionalSignRealFactory, "mount_real", id="MountReal->AdditionalSignReal"),
    pytest.param(MountPlanFactory, SignpostPlanFactory, "mount_plan", id="MountPlan->SignpostPlan"),
    pytest.param(MountRealFactory, SignpostRealFactory, "mount_real", id="MountReal->SignpostReal"),
    pytest.param(SignpostPlanFactory, SignpostPlanFactory, "parent", id="SignpostPlan->child"),
    pytest.param(SignpostRealFactory, SignpostRealFactory, "parent", id="SignpostReal->child"),
    pytest.param(
        TrafficSignPlanFactory, TrafficSignRealFactory, "traffic_sign_plan", id="TrafficSignPlan->TrafficSignReal"
    ),
    pytest.param(
        FurnitureSignpostPlanFactory, FurnitureSignpostPlanFactory, "parent", id="FurnitureSignpostPlan->child"
    ),
    pytest.param(
        FurnitureSignpostRealFactory, FurnitureSignpostRealFactory, "parent", id="FurnitureSignpostReal->child"
    ),
]


# ------------------------------------------------------------------------------
# Helpers and fixtures
# ------------------------------------------------------------------------------


def changelist_url(model: type[Model]) -> str:
    """Builds the admin changelist URL of the given model.

    Args:
        model (type[Model]): Model whose changelist URL is resolved.

    Returns:
        str: URL of the model's admin changelist.
    """
    return reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")


def post_soft_delete(client: Client, *objs: Model, query: str = "", select_across: bool = False) -> HttpResponse:
    """Runs the soft delete action for the given objects via the changelist, as the browser does.

    Args:
        client (Client): Logged in test client that performs the request.
        *objs (Model): Objects to select in the changelist. All must be of the same model.
        query (str): Query string, including the leading "?", appended to the changelist URL.
        select_across (bool): Whether to apply the action to every object the changelist matches,
            like the "Select all N objects" link does, instead of only the selected ones.

    Returns:
        HttpResponse: Response of the changelist POST.
    """
    return client.post(
        changelist_url(type(objs[0])) + query,
        {
            "action": SOFT_DELETE_ACTION,
            ACTION_CHECKBOX_NAME: [str(obj.pk) for obj in objs],
            "index": "0",
            "select_across": "1" if select_across else "0",
        },
    )


def make_child(child_factory: FactoryClass, fk_name: str, parent: Model) -> Model:
    """Creates a child that is linked to the parent only through the given foreign key.

    Args:
        child_factory (FactoryClass): Factory of the child model.
        fk_name (str): Name of the child's foreign key that points to the parent.
        parent (Model): Object the child is linked to.

    Returns:
        Model: The created child.
    """
    kwargs = {fk_name: parent}
    if fk_name != "parent" and "parent" in {f.name for f in child_factory._meta.model._meta.fields}:
        # Additional sign factories create a traffic sign parent by default.
        kwargs["parent"] = None
    return child_factory(**kwargs)


def staff_client(model: type[Model], *actions: str, **user_kwargs: Any) -> tuple[Client, User]:
    """Creates a non-superuser staff user with the given model permissions and logs it in.

    Args:
        model (type[Model]): Model the permissions are for.
        *actions (str): Permission actions to grant, e.g. "view", "change" or "delete".
        **user_kwargs (Any): Extra field values for the created user.

    Returns:
        tuple[Client, User]: Logged in test client and its user.
    """
    user = UserFactory(is_staff=True, **user_kwargs)
    content_type = ContentType.objects.get_for_model(model)
    codenames = [f"{action}_{model._meta.model_name}" for action in actions]
    user.user_permissions.set(Permission.objects.filter(content_type=content_type, codename__in=codenames))
    client = Client()
    client.force_login(user)
    return client, user


@pytest.fixture
def other_user() -> User:
    """Creates a user other than the one performing the admin action.

    Returns:
        User: The created user.
    """
    return UserFactory(username="other_user")


# ------------------------------------------------------------------------------
# Coverage of this module
# ------------------------------------------------------------------------------


def test_every_soft_delete_admin_is_covered() -> None:
    """Ensures that this module covers every admin that offers the soft delete action.

    Returns:
        None
    """
    registry = admin.site._registry
    models_with_mixin = {
        model for model, model_admin in registry.items() if isinstance(model_admin, SoftDeleteAdminMixin)
    }
    soft_deletable_models = {model for model in registry if issubclass(model, SoftDeleteModel)}

    # A soft deletable model registered in admin without the mixin would only offer hard delete.
    assert soft_deletable_models == models_with_mixin
    assert models_with_mixin == set(SOFT_DELETE_FACTORIES)


# ------------------------------------------------------------------------------
# The action itself, for every soft deletable model
# ------------------------------------------------------------------------------


@ALL_MODELS
@pytest.mark.django_db
def test_action_soft_deletes_only_selected_objects(
    admin_client: Client, admin_user: User, factory: FactoryClass
) -> None:
    """Ensures that the action soft deletes the selected objects and leaves the others untouched.

    Args:
        admin_client (Client): Test client logged in as a superuser.
        admin_user (User): The superuser of admin_client.
        factory (FactoryClass): Factory of the model under test.

    Returns:
        None
    """
    selected_1, selected_2, not_selected = factory(), factory(), factory()

    before = timezone.now()
    response = post_soft_delete(admin_client, selected_1, selected_2)
    after = timezone.now()

    assert response.status_code == 302
    for obj in (selected_1, selected_2):
        obj.refresh_from_db()
        assert obj.is_active is False
        assert obj.deleted_by == admin_user
        assert before <= obj.deleted_at <= after

    not_selected.refresh_from_db()
    assert not_selected.is_active is True
    assert not_selected.deleted_at is None
    assert not_selected.deleted_by is None


@ALL_MODELS
@pytest.mark.django_db
def test_action_soft_delete_is_audit_logged_with_actor(
    admin_client: Client, admin_user: User, factory: FactoryClass
) -> None:
    """Ensures that the action writes one audit log update entry with the logged in user as actor.

    Args:
        admin_client (Client): Test client logged in as a superuser.
        admin_user (User): The superuser of admin_client.
        factory (FactoryClass): Factory of the model under test.

    Returns:
        None
    """
    obj = factory()

    post_soft_delete(admin_client, obj)

    update_entries = LogEntry.objects.get_for_object(obj).filter(action=LogEntry.Action.UPDATE)
    assert update_entries.count() == 1
    entry = update_entries.get()
    assert entry.actor == admin_user
    assert entry.changes_dict["is_active"] == ["True", "False"]
    assert LogEntry.objects.get_for_object(obj).filter(action=LogEntry.Action.DELETE).count() == 0


@ALL_MODELS
@pytest.mark.django_db
def test_soft_deleted_objects_are_listed_only_with_soft_deleted_filter(
    admin_client: Client, factory: FactoryClass
) -> None:
    """Ensures that soft deleted objects are hidden from the default list and shown with ?soft_deleted=1.

    Args:
        admin_client (Client): Test client logged in as a superuser.
        factory (FactoryClass): Factory of the model under test.

    Returns:
        None
    """
    active, deleted = factory(), factory()
    url = changelist_url(type(active))

    post_soft_delete(admin_client, deleted)

    default_response = admin_client.get(url)
    assert default_response.status_code == 200
    assert list(default_response.context["cl"].queryset) == [active]

    filtered_response = admin_client.get(url, {"soft_deleted": "1"})
    assert filtered_response.status_code == 200
    assert list(filtered_response.context["cl"].queryset) == [deleted]


@pytest.mark.django_db
def test_action_soft_delete_again_overwrites_deletion_stamp(
    admin_client: Client, admin_user: User, other_user: User
) -> None:
    """Pins current behaviour: re-running the action on an already soft deleted object restamps it.

    This differs from the cascades, which leave already soft deleted children untouched (see
    test_cascade_does_not_restamp_already_soft_deleted_children). Change the assertions if the action is
    made to skip already soft deleted objects.

    Args:
        admin_client (Client): Test client logged in as a superuser.
        admin_user (User): The superuser of admin_client.
        other_user (User): User who soft deleted the object the first time.

    Returns:
        None
    """
    barrier_real = BarrierRealFactory()
    barrier_real.soft_delete(other_user)
    barrier_real.refresh_from_db()
    original_deleted_at = barrier_real.deleted_at

    post_soft_delete(admin_client, barrier_real, query="?soft_deleted=1")

    barrier_real.refresh_from_db()
    assert barrier_real.is_active is False
    assert barrier_real.deleted_by == admin_user
    assert barrier_real.deleted_at > original_deleted_at


# ------------------------------------------------------------------------------
# Permissions
# ------------------------------------------------------------------------------


@ALL_MODELS
@pytest.mark.django_db
def test_action_soft_delete_is_not_available_with_view_permission_only(
    rf: RequestFactory, factory: FactoryClass
) -> None:
    """Ensures that a user with only view permission is not offered the action and cannot run it.

    Args:
        rf (RequestFactory): Request factory for asking the admin which actions it offers.
        factory (FactoryClass): Factory of the model under test.

    Returns:
        None
    """
    obj = factory()
    model = type(obj)
    client, user = staff_client(model, "view", bypass_responsible_entity=True)

    request = rf.get(changelist_url(model))
    request.user = user
    assert SOFT_DELETE_ACTION not in admin.site._registry[model].get_actions(request)

    post_soft_delete(client, obj)

    obj.refresh_from_db()
    assert obj.is_active is True
    assert obj.deleted_at is None
    assert obj.deleted_by is None


@ALL_MODELS
@pytest.mark.parametrize(
    "actions", [("view", "change"), ("view", "delete"), ("view", "change", "delete")], ids="+".join
)
@pytest.mark.django_db
def test_action_soft_delete_is_allowed_with_change_or_delete_permission(
    rf: RequestFactory, factory: FactoryClass, actions: tuple[str, ...]
) -> None:
    """Ensures that change or delete permission alone is enough to run the action.

    Django offers an action when the user has ANY of its allowed_permissions ("change", "delete").

    Args:
        rf (RequestFactory): Request factory for asking the admin which actions it offers.
        factory (FactoryClass): Factory of the model under test.
        actions (tuple[str, ...]): Permission actions granted to the user.

    Returns:
        None
    """
    obj = factory()
    model = type(obj)
    client, user = staff_client(model, *actions, bypass_responsible_entity=True)

    request = rf.get(changelist_url(model))
    request.user = user
    assert SOFT_DELETE_ACTION in admin.site._registry[model].get_actions(request)

    response = post_soft_delete(client, obj)

    assert response.status_code == 302
    obj.refresh_from_db()
    assert obj.is_active is False
    assert obj.deleted_by == user


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(FurnitureSignpostPlanFactory, id="FurnitureSignpostPlan"),
        pytest.param(FurnitureSignpostRealFactory, id="FurnitureSignpostReal"),
    ],
)
@pytest.mark.django_db
def test_action_soft_delete_with_own_responsible_entity(factory: FactoryClass) -> None:
    """Ensures that a user can soft delete a furniture signpost of their own responsible entity.

    Args:
        factory (FactoryClass): Factory of the furniture signpost model under test.

    Returns:
        None
    """
    responsible_entity = ResponsibleEntityFactory()
    obj = factory(responsible_entity=responsible_entity)
    client, user = staff_client(type(obj), "view", "change", "delete")
    user.responsible_entities.add(responsible_entity)

    response = post_soft_delete(client, obj, query="?responsible_entity_permission=True")

    assert response.status_code == 302
    obj.refresh_from_db()
    assert obj.is_active is False
    assert obj.deleted_by == user


# ------------------------------------------------------------------------------
# Cascade to related objects
# ------------------------------------------------------------------------------


@pytest.mark.parametrize(("parent_factory", "child_factory", "fk_name"), CASCADE_CASES)
@pytest.mark.django_db
def test_action_soft_delete_cascades_to_children(
    admin_client: Client, admin_user: User, parent_factory: FactoryClass, child_factory: FactoryClass, fk_name: str
) -> None:
    """Ensures that soft deleting a parent via the action soft deletes its active children too.

    Args:
        admin_client (Client): Test client logged in as a superuser.
        admin_user (User): The superuser of admin_client.
        parent_factory (FactoryClass): Factory of the model the action is run on.
        child_factory (FactoryClass): Factory of the model the soft delete cascades to.
        fk_name (str): Name of the child's foreign key that points to the parent.

    Returns:
        None
    """
    parent = parent_factory()
    children = [make_child(child_factory, fk_name, parent) for _ in range(2)]

    post_soft_delete(admin_client, parent)

    parent.refresh_from_db()
    assert parent.is_active is False
    for child in children:
        child.refresh_from_db()
        assert child.is_active is False
        assert child.deleted_by == admin_user
        assert child.deleted_at is not None

        update_entry = LogEntry.objects.get_for_object(child).get(action=LogEntry.Action.UPDATE)
        assert update_entry.actor == admin_user


@pytest.mark.parametrize(("parent_factory", "child_factory", "fk_name"), CASCADE_CASES)
@pytest.mark.django_db
def test_action_soft_delete_with_select_across_cascades_for_every_listed_parent(
    admin_client: Client, admin_user: User, parent_factory: FactoryClass, child_factory: FactoryClass, fk_name: str
) -> None:
    """Ensures that "Select all N objects" soft deletes every listed parent and their children.

    An already soft deleted parent is not listed by default, so it and its child must stay untouched.

    Args:
        admin_client (Client): Test client logged in as a superuser.
        admin_user (User): The superuser of admin_client.
        parent_factory (FactoryClass): Factory of the model the action is run on.
        child_factory (FactoryClass): Factory of the model the soft delete cascades to.
        fk_name (str): Name of the child's foreign key that points to the parent.

    Returns:
        None
    """
    ticked_parent, unticked_parent, hidden_parent = parent_factory(), parent_factory(), parent_factory()
    listed_children = [make_child(child_factory, fk_name, parent) for parent in (ticked_parent, unticked_parent)]
    hidden_child = make_child(child_factory, fk_name, hidden_parent)
    type(hidden_parent).objects.filter(pk=hidden_parent.pk).update(is_active=False)

    post_soft_delete(admin_client, ticked_parent, select_across=True)

    for obj in (ticked_parent, unticked_parent, *listed_children):
        obj.refresh_from_db()
        assert obj.is_active is False
        assert obj.deleted_by == admin_user

    hidden_parent.refresh_from_db()
    hidden_child.refresh_from_db()
    assert hidden_parent.deleted_by is None
    assert hidden_child.is_active is True


@pytest.mark.parametrize(("parent_factory", "child_factory", "fk_name"), CASCADE_CASES)
@pytest.mark.django_db
def test_action_soft_delete_does_not_cascade_to_children_of_unselected_parents(
    admin_client: Client, parent_factory: FactoryClass, child_factory: FactoryClass, fk_name: str
) -> None:
    """Ensures that the cascade only reaches the children of the selected parents.

    Args:
        admin_client (Client): Test client logged in as a superuser.
        parent_factory (FactoryClass): Factory of the model the action is run on.
        child_factory (FactoryClass): Factory of the model the soft delete cascades to.
        fk_name (str): Name of the child's foreign key that points to the parent.

    Returns:
        None
    """
    selected_parent, other_parent = parent_factory(), parent_factory()
    make_child(child_factory, fk_name, selected_parent)
    other_child = make_child(child_factory, fk_name, other_parent)

    post_soft_delete(admin_client, selected_parent)

    other_parent.refresh_from_db()
    other_child.refresh_from_db()
    assert other_parent.is_active is True
    assert other_child.is_active is True
    assert other_child.deleted_at is None
    assert other_child.deleted_by is None


@pytest.mark.parametrize(("parent_factory", "child_factory", "fk_name"), CASCADE_CASES)
@pytest.mark.django_db
def test_cascade_does_not_restamp_already_soft_deleted_children(
    admin_client: Client, other_user: User, parent_factory: FactoryClass, child_factory: FactoryClass, fk_name: str
) -> None:
    """Ensures that a child soft deleted earlier keeps its original deletion time and user.

    Args:
        admin_client (Client): Test client logged in as a superuser.
        other_user (User): User who soft deleted the child before the action is run.
        parent_factory (FactoryClass): Factory of the model the action is run on.
        child_factory (FactoryClass): Factory of the model the soft delete cascades to.
        fk_name (str): Name of the child's foreign key that points to the parent.

    Returns:
        None
    """
    parent = parent_factory()
    child = make_child(child_factory, fk_name, parent)
    child.soft_delete(other_user)
    child.refresh_from_db()
    original_deleted_at = child.deleted_at

    post_soft_delete(admin_client, parent)

    parent.refresh_from_db()
    child.refresh_from_db()
    assert parent.is_active is False
    assert child.is_active is False
    assert child.deleted_by == other_user
    assert child.deleted_at == original_deleted_at


@pytest.mark.parametrize(
    ("traffic_sign_factory", "additional_sign_factory", "signpost_factory", "signpost_fk_name"),
    [
        pytest.param(
            TrafficSignPlanFactory, AdditionalSignPlanFactory, SignpostPlanFactory, "signpost_plan", id="Plan"
        ),
        pytest.param(
            TrafficSignRealFactory, AdditionalSignRealFactory, SignpostRealFactory, "signpost_real", id="Real"
        ),
    ],
)
@pytest.mark.django_db
def test_traffic_sign_soft_delete_does_not_cascade_to_additional_signs_moved_to_signpost(
    admin_client: Client,
    traffic_sign_factory: FactoryClass,
    additional_sign_factory: FactoryClass,
    signpost_factory: FactoryClass,
    signpost_fk_name: str,
) -> None:
    """Ensures that additional signs already moved to a signpost are not soft deleted with the traffic sign.

    Args:
        admin_client (Client): Test client logged in as a superuser.
        traffic_sign_factory (FactoryClass): Factory of the traffic sign model the action is run on.
        additional_sign_factory (FactoryClass): Factory of the matching additional sign model.
        signpost_factory (FactoryClass): Factory of the matching signpost model.
        signpost_fk_name (str): Name of the additional sign's foreign key that points to the signpost.

    Returns:
        None
    """
    traffic_sign = traffic_sign_factory()
    signpost = signpost_factory()
    moved_to_signpost = additional_sign_factory(parent=traffic_sign, **{signpost_fk_name: signpost})
    still_on_traffic_sign = additional_sign_factory(parent=traffic_sign)

    post_soft_delete(admin_client, traffic_sign)

    moved_to_signpost.refresh_from_db()
    still_on_traffic_sign.refresh_from_db()
    signpost.refresh_from_db()
    assert moved_to_signpost.is_active is True
    assert still_on_traffic_sign.is_active is False
    assert signpost.is_active is True


@pytest.mark.parametrize(("parent_factory", "related_factory", "fk_name"), NO_CASCADE_CASES)
@pytest.mark.django_db
def test_action_soft_delete_does_not_cascade_over_other_relations(
    admin_client: Client, parent_factory: FactoryClass, related_factory: FactoryClass, fk_name: str
) -> None:
    """Pins the relations that soft delete does not follow: the related object stays active and linked.

    Args:
        admin_client (Client): Test client logged in as a superuser.
        parent_factory (FactoryClass): Factory of the model the action is run on.
        related_factory (FactoryClass): Factory of the model that refers to the parent.
        fk_name (str): Name of the related object's foreign key that points to the parent.

    Returns:
        None
    """
    parent = parent_factory()
    related = related_factory(**{fk_name: parent})

    post_soft_delete(admin_client, parent)

    parent.refresh_from_db()
    related.refresh_from_db()
    assert parent.is_active is False
    assert related.is_active is True
    assert related.deleted_at is None
    assert getattr(related, fk_name) == parent
