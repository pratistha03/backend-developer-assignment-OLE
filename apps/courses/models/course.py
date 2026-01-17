from enum import unique
from django.db import models
from django.core.validators import MinValueValidator
from apps.base.models import BaseModel
from apps.auth.models import User, Role


class Course(BaseModel):    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    code = models.CharField(max_length=15, unique=True)
    title = models.CharField(max_length=255)
    short_description = models.TextField(max_length=500)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses', limit_choices_to={'role': Role.INSTRUCTOR})
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'courses'
    
    def __str__(self):
        return self.title
    
    @property
    def is_published(self):
        return self.status == 'published'

    def save(self, *args, **kwargs):
        if not self.pk:
            last_course = Course.objects.order_by('-id').first()
            last_course_no = 0
            if last_course:
                last_course_code = last_course.code
                try:
                    last_course_no = int(last_course_code.split('-')[-1])
                except (IndexError, ValueError):
                    pass  
            code = 'COURSE'
            new_course_no = last_course_no + 1
            new_course_code = f"{code}-{new_course_no:04d}"
            self.code = new_course_code
        super().save(*args, **kwargs)





