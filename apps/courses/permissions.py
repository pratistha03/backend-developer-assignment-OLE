from rest_framework import permissions
from apps.auth.models import Role


class IsInstructor(permissions.BasePermission):
    message = "Only instructors can access this resource."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == Role.INSTRUCTOR
        )


class IsStudent(permissions.BasePermission):
    message = "Only students can access this resource."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == Role.STUDENT
        )


class IsCourseOwner(permissions.BasePermission):
    message = "You can only manage your own courses."
    
    def has_object_permission(self, request, view, obj):
        return obj.instructor == request.user


class IsEnrollmentOwner(permissions.BasePermission):
    message = "You can only access your own enrollments."
    
    def has_object_permission(self, request, view, obj):
        return obj.student == request.user
