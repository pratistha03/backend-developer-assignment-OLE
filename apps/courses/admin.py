from django.contrib import admin
from apps.courses.models.course import Course
from apps.courses.models.lesson import Lesson, LessonProgress
from apps.courses.models.enrollment import Enrollment

admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(LessonProgress)
admin.site.register(Enrollment)
