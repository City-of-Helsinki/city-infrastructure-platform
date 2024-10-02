from rest_framework import mixins, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response


class UserCreateMixin(mixins.CreateModelMixin):
    """Automatically apply user information to model from the request on create."""

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)


class UserUpdateMixin(mixins.UpdateModelMixin):
    """Automatically apply user information to model from the request on update."""

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class SoftDeleteMixin(mixins.DestroyModelMixin):
    """Soft delete mixin. Marks the entity as deleted instead of deleting it."""

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
