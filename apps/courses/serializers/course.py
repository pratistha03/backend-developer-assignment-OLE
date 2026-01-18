from rest_framework import serializers
from apps.courses.models.course import Course
from apps.courses.serializers.lesson import LessonSerializer

class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    instructor_name = serializers.CharField(source='instructor.full_name', read_only=True)
    lesson_count = serializers.IntegerField(source='lessons.count', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'code', 'title', 'short_description', 'instructor', 'instructor_name',
            'status', 'lesson_count', 'lessons', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'instructor_name','instructor', 'lesson_count', 'code']


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'short_description', 'code', 'status']
        read_only_fields = ['id', 'code', 'status']
    
    def create(self, validated_data):
        validated_data['instructor'] = self.context['request'].user
        validated_data['status'] = 'draft'
        return super().create(validated_data)






