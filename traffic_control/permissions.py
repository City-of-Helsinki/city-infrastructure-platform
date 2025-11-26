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


class ResponsibleEntityPermission(BasePermission):
    message = "You do not have permissions to this Responsible Entity set"

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        if request.user.is_authenticated and (
            request.user.has_bypass_responsible_entity_permission()
            or request.user.can_create_responsible_entity_devices()
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return request.user.has_responsible_entity_permission(obj.responsible_entity)
