from rest_framework import permissions
from apps.auth.models import Role


class IsInstructor(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == Role.INSTRUCTOR
        )


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == Role.STUDENT
        )


class IsCourseOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.instructor == request.user


class IsEnrollmentOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.student == request.user
