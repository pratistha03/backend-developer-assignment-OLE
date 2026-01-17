from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.courses.views import (
    CourseViewSet,
    LessonViewSet,
    EnrollmentViewSet,
    LessonProgressViewSet,
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'progress', LessonProgressViewSet, basename='lesson-progress')

urlpatterns = [
    path('api/', include(router.urls)),
]
