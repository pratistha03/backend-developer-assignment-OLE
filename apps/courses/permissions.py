from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from apps.auth.models import Role


class IsInstructor(permissions.BasePermission):
    message = "You do not have permission to perform this action. Only instructors can access this resource."
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role != Role.INSTRUCTOR:
            return False
        return True


class IsStudent(permissions.BasePermission):
    message = "You do not have permission to perform this action. Only students can access this resource."
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role != Role.STUDENT:
            return False
        return True


class IsCourseOwner(permissions.BasePermission):
    message = "You do not have permission to perform this action. You can only manage your own courses."
    
    def has_object_permission(self, request, view, obj):
        if obj.instructor != request.user:
            raise PermissionDenied(self.message)
        return True


class IsEnrollmentOwner(permissions.BasePermission):
    message = "You do not have permission to access this enrollment. You can only access your own enrollments."
    
    def has_object_permission(self, request, view, obj):
        if obj.student != request.user:
            raise PermissionDenied(self.message)
        return True
