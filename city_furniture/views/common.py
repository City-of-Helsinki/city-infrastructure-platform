from rest_framework import permissions


class ResponsibleEntityPermission(permissions.BasePermission):
    message = "You do not have permissions to this Responsible Entity set"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_superuser or request.user.bypass_responsible_entity:
            return True

        if request.user.responsible_entities.exists():
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_superuser or request.user.bypass_responsible_entity:
            return True

        if obj.responsible_entity is None:
            return False

        return obj.responsible_entity.get_ancestors(include_self=True).filter(users=request.user).exists()
