from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.courses.models.course import Course
from apps.courses.models.lesson import Lesson, LessonProgress
from apps.courses.models.enrollment import Enrollment
from apps.courses.serializers.course import CourseSerializer, CourseCreateSerializer
from apps.courses.serializers.lesson import LessonSerializer, LessonCreateSerializer, LessonBulkCreateSerializer, LessonProgressSerializer
from apps.courses.serializers.enrollment import EnrollmentSerializer, EnrollmentProgressSerializer
from apps.courses.permissions import IsInstructor, IsStudent, IsCourseOwner, IsEnrollmentOwner
from apps.auth.models import Role


class CourseViewSet(viewsets.ModelViewSet):  
    http_method_names = ['get', 'post', 'patch', 'delete']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CourseCreateSerializer
        return CourseSerializer
    
    def get_queryset(self):
        user = self.request.user 
        if user.role == Role.INSTRUCTOR:
            return Course.objects.filter(instructor=user)
        elif user.role == Role.STUDENT:
            return Course.objects.filter(status='published')
        return Course.objects.none()
    
    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated(), IsInstructor()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsCourseOwner()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user, status='draft')
    
    @extend_schema(
        operation_id='course_publish',
        summary='Publish a draft course',
        description='Publish a draft course. Only draft courses can be published.',
        request=None,
        responses=OpenApiResponse(description='Course published successfully')
    )
    @action(detail=True, methods=['patch'], permission_classes=[IsCourseOwner])
    def publish(self, request, pk=None):
        course = self.get_object()
        if course.status != 'draft':
            return Response(
                {'error': 'Only draft courses can be published'},
                status=status.HTTP_400_BAD_REQUEST
            )
        course.status = 'published'
        course.save()
        return Response({'status': 'Course published successfully'}, status=status.HTTP_200_OK)




class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    
    def get_queryset(self):
        user = self.request.user
        course_id = self.request.query_params.get('course', None)
        
        if user.role == Role.INSTRUCTOR:
            if course_id:
                return Lesson.objects.filter(course_id=course_id, course__instructor=user)
            return Lesson.objects.filter(course__instructor=user)
        elif user.role == Role.STUDENT:
            enrolled_course_ids = Enrollment.objects.filter(
                student=user
            ).values_list('course_id', flat=True)
            queryset = Lesson.objects.filter(course_id__in=enrolled_course_ids)
            if course_id:
                queryset = queryset.filter(course_id=course_id)
            return queryset
        return Lesson.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LessonCreateSerializer
        elif self.action == 'bulk_create':
            return LessonBulkCreateSerializer
        return LessonSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'bulk_create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsInstructor()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        
        course_id = self.request.data.get('course')
        if not course_id:
            raise ValidationError(
                {"course": "Course ID is required"}
            )
        
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise NotFound("Course not found")
        
        if course.instructor != self.request.user:
            raise PermissionDenied("You can only add lessons to your own courses")
        
        serializer.save(course=course)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsInstructor])
    def bulk_create(self, request):
        """
        Create multiple lessons for a course at once.
        
        Request body:
        {
            "course": 1,
            "lessons": [
                {"title": "Lesson 1", "content": "Content 1", "order": 1},
                {"title": "Lesson 2", "content": "Content 2", "order": 2}
            ]
        }
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        lessons = serializer.save()
        
        response_serializer = LessonSerializer(lessons, many=True)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class EnrollmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsStudent]
    http_method_names = ['get', 'post']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EnrollmentProgressSerializer
        return EnrollmentSerializer
    
    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user)
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsStudent()]
        return [IsAuthenticated(), IsStudent(), IsEnrollmentOwner()]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        total_lessons = instance.course.lessons.count()
        completed_lessons = LessonProgress.objects.filter(
            enrollment=instance,
            completed=True
        ).count()
        completion_percentage = round((completed_lessons / total_lessons * 100) if total_lessons > 0 else 0.0, 2)
        
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['total_lessons'] = total_lessons
        data['completed_lessons'] = completed_lessons
        data['completion_percentage'] = completion_percentage
        
        return Response(data, status=status.HTTP_200_OK)
    
    def perform_create(self, serializer):
        course_id = self.request.data.get('course')
        if not course_id:
            raise ValidationError({"course": "Course ID is required"})
        
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise NotFound("Course not found")
        
        if course.status != 'published':
            raise ValidationError({"course": "Only published courses can be enrolled in"})
        
        if course.instructor == self.request.user:
            raise ValidationError({"course": "Instructors may not enroll in their own courses"})
        
        if Enrollment.objects.filter(student=self.request.user, course=course).exists():
            raise ValidationError({"course": "You are already enrolled in this course"})
        
        enrollment = serializer.save(student=self.request.user, course=course)
        
        lessons = course.lessons.all()
        for lesson in lessons:
            LessonProgress.objects.create(
                enrollment=enrollment,
                lesson=lesson,
                completed=False
            )




class LessonProgressViewSet(viewsets.ModelViewSet):
    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated, IsStudent, IsEnrollmentOwner]
    
    def get_queryset(self):
        return LessonProgress.objects.filter(enrollment__student=self.request.user)
    
    def _validate_sequential_completion(self, enrollment, lesson):
        all_lessons = enrollment.course.lessons.all().order_by('order')
        current_order = lesson.order
        
        previous_lessons = all_lessons.filter(order__lt=current_order)
        
        if previous_lessons.exists():
            completed_lesson_ids = LessonProgress.objects.filter(
                enrollment=enrollment,
                completed=True
            ).values_list('lesson_id', flat=True)
            
            incomplete_previous = previous_lessons.exclude(id__in=completed_lesson_ids)
            
            if incomplete_previous.exists():
                incomplete_lesson = incomplete_previous.first()
                raise ValidationError({
                    "lesson": f"You must complete lesson {incomplete_lesson.order} ({incomplete_lesson.title}) before completing this lesson."
                })
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance.enrollment.student != request.user:
            raise PermissionDenied("You can only update your own progress")
        
        if 'lesson' in request.data:
            lesson_id = request.data.get('lesson')
            if lesson_id != instance.lesson.id:
                try:
                    lesson = Lesson.objects.get(id=lesson_id)
                    if lesson.course != instance.enrollment.course:
                        raise ValidationError({"lesson": "Lesson does not belong to the enrolled course"})
                except Lesson.DoesNotExist:
                    raise NotFound("Lesson not found")
        
        if request.data.get('completed') and not instance.completed:
            self._validate_sequential_completion(instance.enrollment, instance.lesson)
        
        response = super().update(request, *args, **kwargs)
        
        progress = self.get_object()
        if progress.completed:
            self._check_course_completion(progress.enrollment)
        
        return response
    
    @extend_schema(
        operation_id='lesson_progress_complete',
        summary='Mark a lesson as completed',
        description='Mark a lesson as completed. This is a convenience endpoint that sets the lesson progress to completed.',
        responses={
            200: LessonProgressSerializer,
            403: OpenApiResponse(description='Forbidden - Not the enrollment owner'),
            404: OpenApiResponse(description='Not Found - Progress record does not exist')
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStudent])
    def complete(self, request, pk=None):
        progress = self.get_object()
        
        if progress.enrollment.student != request.user:
            raise PermissionDenied("You can only update your own progress")
        
        if progress.completed:
            return Response(
                {'message': 'Lesson is already completed'},
                status=status.HTTP_200_OK
            )
        
        self._validate_sequential_completion(progress.enrollment, progress.lesson)
        
        progress.completed = True
        progress.completed_at = timezone.now()
        progress.save()
        
        # Check if course is completed
        self._check_course_completion(progress.enrollment)
        
        serializer = self.get_serializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def _check_course_completion(self, enrollment):
        total_lessons = enrollment.course.lessons.count()
        completed_lessons = LessonProgress.objects.filter(
            enrollment=enrollment,
            completed=True
        ).count()
        
        if total_lessons > 0 and completed_lessons == total_lessons:
            # Mark enrollment as completed
            if not enrollment.completed_at:
                enrollment.completed_at = timezone.now()
                enrollment.save()
            
            # Trigger async task
            from apps.courses.tasks import send_course_completion_notification
            send_course_completion_notification.delay(enrollment.id)
