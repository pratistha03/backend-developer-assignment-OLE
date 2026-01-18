from rest_framework import serializers
from apps.courses.models.lesson import Lesson, LessonProgress


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'order', 'course', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'course']



class LessonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'order', 'course']
    
    def create(self, validated_data):
        validated_data['course'] = self.context['course']
        return super().create(validated_data)



class LessonBulkCreateSerializer(serializers.Serializer):
    course = serializers.IntegerField(write_only=True)
    lessons = LessonSerializer(many=True)
    
    def validate_lessons(self, value):
        orders = [lesson.get('order') for lesson in value if lesson.get('order')]
        if len(orders) != len(set(orders)):
            raise serializers.ValidationError("Lesson orders must be unique within the request.")
        return value
    
    def create(self, validated_data):
        course_id = validated_data.pop('course')
        lessons_data = validated_data.pop('lessons')
        
        from apps.courses.models.course import Course
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise serializers.ValidationError({"course": "Course not found"})
        
        if course.instructor != self.context['request'].user:
            raise serializers.ValidationError({"course": "You can only add lessons to your own courses"})
        
        existing_orders = set(course.lessons.values_list('order', flat=True))
        new_orders = [lesson['order'] for lesson in lessons_data]
        conflicting_orders = set(new_orders) & existing_orders
        if conflicting_orders:
            raise serializers.ValidationError(
                {"lessons": f"Lesson orders {sorted(conflicting_orders)} already exist in this course."}
            )
        
        lessons = []
        for lesson_data in lessons_data:
            lesson = Lesson.objects.create(course=course, **lesson_data)
            lessons.append(lesson)
        
        return lessons



class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'enrollment', 'lesson', 'lesson_title',
            'completed', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'completed_at', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        if validated_data.get('completed') and not instance.completed:
            from django.utils import timezone
            validated_data['completed_at'] = timezone.now()
        return super().update(instance, validated_data)

