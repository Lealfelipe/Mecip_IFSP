from rest_framework import permissions

from mecip.permissions import can_answer_report, can_manage_records


class RoleBasedModelPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if getattr(view, 'action', None) == 'responder':
            return True
        return can_manage_records(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if getattr(view, 'action', None) == 'responder':
            return True
        return can_manage_records(request.user)
