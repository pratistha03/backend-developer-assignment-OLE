from django.db import models
from apps.auth.models import User, Role
from apps.courses.models import Course
from apps.base.models import BaseModel


class Enrollment(BaseModel): 
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments', limit_choices_to={'role': Role.STUDENT})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
        db_table = 'enrollments'
    
    @property
    def is_completed(self):
        return self.completed_at is not None
    
    def __str__(self):
        return f"{self.student.email} - {self.course.title}"
