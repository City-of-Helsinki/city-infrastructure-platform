from rest_framework.permissions import BasePermission, IsAdminUser, SAFE_METHODS


class IsAdminUserOrReadOnly(IsAdminUser):
    def has_permission(self, request, view):
        is_admin = super().has_permission(request, view)
        return request.method in SAFE_METHODS or is_admin


class ObjectInsideOperationalAreaOrAnonReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user

        if request.method in SAFE_METHODS:
            return True
        if user.is_anonymous:
            return False

        # Unsafe operation is being performed by authenticated user. Operation
        # is allowed only if the object is located within user's operational
        # area or if user is superuser or operational area is bypassed for
        # current user.
        return request.user.location_is_in_operational_area(obj.location)
