from datetime import datetime

from django.utils.timezone import make_aware
from rest_framework import mixins, status
from rest_framework.response import Response


class SoftDeleteMixin(mixins.DestroyModelMixin):
    """ Soft delete mixin"""

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.deleted_by = request.user
        instance.deleted_at = make_aware(datetime.now())
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
