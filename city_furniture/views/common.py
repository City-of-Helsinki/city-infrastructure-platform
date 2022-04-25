from rest_framework import permissions


class ResponsibleEntityPermission(permissions.BasePermission):
    message = "You do not have permissions to this Responsible Entity set"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.has_bypass_responsible_entity_permission() or request.user.responsible_entities.exists():
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.has_bypass_responsible_entity_permission(obj)
