from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from apps.base.models import BaseModel


class Role(models.TextChoices):
    STUDENT = 'Student', 'Student'
    INSTRUCTOR = 'Instructor', 'Instructor'


class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier"""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', Role.INSTRUCTOR)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, BaseModel):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices)
    # is_active is already provided by AbstractUser

    username = None  # since we're using email
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'role']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'   
        ordering = ['-created_at']
        db_table = 'users'

    def __str__(self):
        return self.email
    
    @property
    def is_student(self):
        return self.role == Role.STUDENT
    
    @property
    def is_instructor(self):
        return self.role == Role.INSTRUCTOR