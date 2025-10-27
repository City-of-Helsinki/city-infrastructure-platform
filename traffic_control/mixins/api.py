import logging

from auditlog.context import set_actor
from rest_framework import mixins, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def is_usercreatable_model(model):
    return hasattr(model, "created_by")


def is_userupdatable_model(model):
    return hasattr(model, "updated_by")


def is_softdeletable_model(object_or_model):
    model = object_or_model
    return hasattr(model, "soft_delete")


class UserCreateMixin(mixins.CreateModelMixin):
    """Automatically apply user information to model from the request on create if model is user creatable
    Auditlog set_actor is also set to the request user during creation, otherwise auditlog would log None as actor.
    """

    def perform_create(self, serializer):
        user = self.request.user
        with set_actor(user):
            if is_usercreatable_model(serializer.Meta.model):
                serializer.save(created_by=self.request.user, updated_by=self.request.user)
            else:
                logger.warning(
                    "Model %s does not support created_by field, saving anyways", serializer.Meta.model.__name__
                )
                serializer.save()


class UserUpdateMixin(mixins.UpdateModelMixin):
    """Automatically apply user information to model from the request on update if model is user updatable.
    Auditlog set_actor is also set to the request user during update, otherwise auditlog would log None as actor.
    """

    def perform_update(self, serializer):
        user = self.request.user
        with set_actor(user):
            if is_userupdatable_model(serializer.Meta.model):
                serializer.save(updated_by=self.request.user)
            else:
                logger.warning(
                    "Model %s does not support updated_by field, saving anyways", serializer.Meta.model.__name__
                )
                serializer.save()


class SoftDeleteMixin(mixins.DestroyModelMixin):
    """Soft delete mixin. Marks the entity as deleted instead of deleting if entity is softdeletable.
    Auditlog set_actor is also set to the request user during deletion, otherwise auditlog would log None as actor.
    """

    def destroy(self, request, *args, **kwargs):
        user = request.user
        with set_actor(user):
            instance = self.get_object()
            if is_softdeletable_model(instance):
                instance.soft_delete(user)
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                logger.warning("Model %s does not support soft delete, doing full delete", instance.__class__.__name__)
                super().perform_destroy(instance)
                return Response(status=status.HTTP_204_NO_CONTENT)


class AuditLoggingMixin(UserCreateMixin, UserUpdateMixin, SoftDeleteMixin):
    """
    Mixin that adds audit logging functionality to create, update and delete operations.
    Combines UserCreateMixin, UserUpdateMixin and SoftDeleteMixin.
    """


class ReplaceableModelMixin(mixins.RetrieveModelMixin):
    def get_object(self):
        """
        Get object without filtering, PlanReplacementFilterSet sets default value for is_replaced to False
        without this replaced objects would never be fetched.
        """
        obj = get_object_or_404(queryset=self.get_queryset(), pk=self.kwargs["pk"])
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
