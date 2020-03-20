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


class Point3DFieldAdminMixin:
    """A mixin class that shows a map for 3d geometries.

    Django's default behaviour is to use a text field for 3d geometries.
    The class must be used together with traffic_control.forms.Point3DFieldForm
    in order to save 3d geometry to model instances
    """

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "location":
            kwargs["widget"] = self.get_map_widget(db_field)
            return db_field.formfield(**kwargs)

        return super().formfield_for_dbfield(db_field, request, **kwargs)
