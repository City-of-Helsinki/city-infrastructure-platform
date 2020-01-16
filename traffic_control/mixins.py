from datetime import datetime

from django.utils.timezone import make_aware
from rest_framework import mixins, status
from rest_framework.response import Response


class UserCreateMixin(mixins.CreateModelMixin):
    """ Automatically apply user information to model from the request on create. """

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)


class UserUpdateMixin(mixins.UpdateModelMixin):
    """ Automatically apply user information to model from the request on update. """

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class SoftDeleteMixin(mixins.DestroyModelMixin):
    """ Soft delete mixin. Marks the entity as deleted instead of deleting it. """

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.deleted_by = request.user
        instance.deleted_at = make_aware(datetime.now())
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
