from rest_framework import serializers
from apps.courses.models.enrollment import Enrollment


class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'student_name', 'course', 'course_title',
            'enrolled_at', 'completed_at', 'is_completed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'student', 'enrolled_at', 'completed_at', 'is_completed', 'created_at', 'updated_at']


class EnrollmentProgressSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    total_lessons = serializers.IntegerField(read_only=True)
    completed_lessons = serializers.IntegerField(read_only=True)
    completion_percentage = serializers.FloatField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'course_title', 'enrolled_at', 'completed_at',
            'is_completed', 'total_lessons', 'completed_lessons',
            'completion_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'enrolled_at', 'completed_at', 'is_completed',
                          'total_lessons', 'completed_lessons', 'completion_percentage',
                          'created_at', 'updated_at']