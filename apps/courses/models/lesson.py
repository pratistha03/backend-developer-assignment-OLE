from django.db import models
from django.core.validators import MinValueValidator
from apps.courses.models import Course, Enrollment
from apps.base.models import BaseModel

class Lesson(BaseModel):
    course = models.ForeignKey( Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Order of lesson within the course")
    
    class Meta:
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
        db_table = 'lessons'
    
    def __str__(self):
        return f"{self.course.title} - Lesson {self.order}: {self.title}"



class LessonProgress(BaseModel):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progresses')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progresses')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['enrollment', 'lesson']
        db_table = 'lesson_progress'
    
    def __str__(self):
        status = "Completed" if self.completed else "In Progress"
        return f"{self.enrollment.student.email} - {self.lesson.title} ({status})"
