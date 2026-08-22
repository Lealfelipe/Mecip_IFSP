from rest_framework import permissions

from mecip.models import Questionnaire, Report
from mecip.permissions import (
    can_manage_records,
    can_view_questionnaire,
    can_view_report_questionnaire,
)


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
        if getattr(view, 'action', None) == 'responder':
            return can_view_questionnaire(request.user, obj)

        if request.method in permissions.SAFE_METHODS:
            if isinstance(obj, Report):
                return can_view_report_questionnaire(request.user, obj)
            if isinstance(obj, Questionnaire):
                return can_view_questionnaire(request.user, obj)
            return True

        return can_manage_records(request.user)
