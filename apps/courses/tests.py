"""
Comprehensive tests for courses app covering:
- Core business rules
- Authorization boundaries
- Enrollment and completion logic
- Async task triggering
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.courses.models.course import Course
from apps.courses.models.lesson import Lesson, LessonProgress
from apps.courses.models.enrollment import Enrollment
from apps.auth.models import Role

User = get_user_model()


class CourseBusinessRulesTestCase(APITestCase):
    
    def setUp(self):
        # Set up test data
        self.instructor = User.objects.create_user(
            email='instructor@test.com',
            password='testpass123',
            full_name='Test Instructor',
            role=Role.INSTRUCTOR
        )
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            full_name='Test Student',
            role=Role.STUDENT
        )
        self.instructor_token = RefreshToken.for_user(self.instructor)
        self.student_token = RefreshToken.for_user(self.student)
    
    def test_course_created_in_draft_state(self):
        # Courses should be created in draft state
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.instructor_token.access_token}')
        
        response = self.client.post('/api/courses/', {
            'title': 'Test Course',
            'short_description': 'Test description'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'draft')
        course = Course.objects.get(id=response.data['id'])
        self.assertEqual(course.status, 'draft')
    
    def test_course_code_auto_generated(self):
        # Course code should be auto-generated
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.instructor_token.access_token}')
        
        response = self.client.post('/api/courses/', {
            'title': 'Test Course',
            'short_description': 'Test description'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('code', response.data)
        self.assertTrue(response.data['code'].startswith('COURSE-'))
    
    def test_only_published_courses_visible_to_students(self):
        # Students should only see published courses
        # Create draft and published courses
        draft_course = Course.objects.create(
            title='Draft Course',
            short_description='Draft',
            instructor=self.instructor,
            status='draft'
        )
        published_course = Course.objects.create(
            title='Published Course',
            short_description='Published',
            instructor=self.instructor,
            status='published'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token.access_token}')
        response = self.client.get('/api/courses/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course_ids = [c['id'] for c in response.data['results']]
        self.assertNotIn(draft_course.id, course_ids)
        self.assertIn(published_course.id, course_ids)
    
    def test_instructors_see_only_own_courses(self):
        # Instructors should only see their own courses
        other_instructor = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            full_name='Other Instructor',
            role=Role.INSTRUCTOR
        )
        
        own_course = Course.objects.create(
            title='Own Course',
            short_description='Own',
            instructor=self.instructor,
            status='draft'
        )
        other_course = Course.objects.create(
            title='Other Course',
            short_description='Other',
            instructor=other_instructor,
            status='draft'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.instructor_token.access_token}')
        response = self.client.get('/api/courses/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course_ids = [c['id'] for c in response.data['results']]
        self.assertIn(own_course.id, course_ids)
        self.assertNotIn(other_course.id, course_ids)


class AuthorizationBoundaryTestCase(APITestCase):    
    def setUp(self):
        # Set up test data
        self.instructor = User.objects.create_user(
            email='instructor@test.com',
            password='testpass123',
            full_name='Test Instructor',
            role=Role.INSTRUCTOR
        )
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            full_name='Test Student',
            role=Role.STUDENT
        )
        self.other_instructor = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            full_name='Other Instructor',
            role=Role.INSTRUCTOR
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            short_description='Test',
            instructor=self.instructor,
            status='draft'
        )
        
        self.instructor_token = RefreshToken.for_user(self.instructor)
        self.student_token = RefreshToken.for_user(self.student)
        self.other_instructor_token = RefreshToken.for_user(self.other_instructor)
    
    def test_students_cannot_create_courses(self):
        # Students should not be able to create courses
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token.access_token}')
        
        response = self.client.post('/api/courses/', {
            'title': 'Test Course',
            'short_description': 'Test description'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_students_cannot_update_courses(self):
        # Students should not be able to update courses
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token.access_token}')
        
        response = self.client.patch(f'/api/courses/{self.course.id}/', {
            'title': 'Updated Title'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_instructors_cannot_update_other_instructors_courses(self):
        # Instructors should not be able to update courses they don't own
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_instructor_token.access_token}')
        
        response = self.client.patch(f'/api/courses/{self.course.id}/', {
            'title': 'Updated Title'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_instructors_cannot_enroll_in_courses(self):
        # Instructors should not be able to enroll in courses
        self.course.status = 'published'
        self.course.save()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.instructor_token.access_token}')
        
        response = self.client.post('/api/enrollments/', {
            'course': self.course.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_students_cannot_create_lessons(self):
        # Students should not be able to create lessons
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token.access_token}')
        
        response = self.client.post('/api/lessons/', {
            'title': 'Test Lesson',
            'content': 'Content',
            'order': 1,
            'course': self.course.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_students_can_only_see_own_enrollments(self):
        # Students should only see their own enrollments
        other_student = User.objects.create_user(
            email='otherstudent@test.com',
            password='testpass123',
            full_name='Other Student',
            role=Role.STUDENT
        )
        
        self.course.status = 'published'
        self.course.save()
        
        own_enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course
        )
        other_enrollment = Enrollment.objects.create(
            student=other_student,
            course=self.course
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token.access_token}')
        response = self.client.get('/api/enrollments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrollment_ids = [e['id'] for e in response.data['results']]
        self.assertIn(own_enrollment.id, enrollment_ids)
        self.assertNotIn(other_enrollment.id, enrollment_ids)
    
    def test_unauthenticated_users_cannot_access_protected_endpoints(self):
        # Unauthenticated users should receive 401
        response = self.client.get('/api/courses/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.get('/api/enrollments/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.get('/api/progress/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EnrollmentLogicTestCase(APITestCase):
    def setUp(self):
        # Set up test data
        self.instructor = User.objects.create_user(
            email='instructor@test.com',
            password='testpass123',
            full_name='Test Instructor',
            role=Role.INSTRUCTOR
        )
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            full_name='Test Student',
            role=Role.STUDENT
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            short_description='Test',
            instructor=self.instructor,
            status='published'
        )
        
        self.lesson1 = Lesson.objects.create(
            course=self.course,
            title='Lesson 1',
            content='Content 1',
            order=1
        )
        self.lesson2 = Lesson.objects.create(
            course=self.course,
            title='Lesson 2',
            content='Content 2',
            order=2
        )
        self.lesson3 = Lesson.objects.create(
            course=self.course,
            title='Lesson 3',
            content='Content 3',
            order=3
        )
        
        self.student_token = RefreshToken.for_user(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token.access_token}')
    
    def test_cannot_enroll_in_draft_course(self):
        # Students should not be able to enroll in draft courses
        draft_course = Course.objects.create(
            title='Draft Course',
            short_description='Draft',
            instructor=self.instructor,
            status='draft'
        )
        
        response = self.client.post('/api/enrollments/', {
            'course': draft_course.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('course', response.data.get('errors', {}))
    
    def test_cannot_enroll_twice_in_same_course(self):
        # Students should not be able to enroll twice in the same course
        # First enrollment
        response1 = self.client.post('/api/enrollments/', {
            'course': self.course.id
        })
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Second enrollment attempt
        response2 = self.client.post('/api/enrollments/', {
            'course': self.course.id
        })
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('course', response2.data.get('errors', {}))
    
    def test_enrollment_creates_lesson_progress_records(self):
        # Enrollment should create progress records for all lessons
        response = self.client.post('/api/enrollments/', {
            'course': self.course.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        enrollment_id = response.data['id']
        enrollment = Enrollment.objects.get(id=enrollment_id)
        
        # Check that progress records were created
        progress_count = LessonProgress.objects.filter(enrollment=enrollment).count()
        self.assertEqual(progress_count, 3)  # Should have 3 lessons
        
        # Check all progress records are incomplete
        incomplete_count = LessonProgress.objects.filter(
            enrollment=enrollment,
            completed=False
        ).count()
        self.assertEqual(incomplete_count, 3)
    
    def test_sequential_lesson_completion_required(self):
        # Lessons must be completed in sequential order
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course
        )
        
        # Create progress records
        progress1 = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=self.lesson1,
            completed=False
        )
        progress2 = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=self.lesson2,
            completed=False
        )
        progress3 = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=self.lesson3,
            completed=False
        )
        
        # Try to complete lesson 2 before lesson 1 (should fail)
        response = self.client.patch(f'/api/progress/{progress2.id}/', {
            'completed': True
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('lesson', response.data.get('errors', {}))
        
        # Complete lesson 1 (should succeed)
        response = self.client.patch(f'/api/progress/{progress1.id}/', {
            'completed': True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Now complete lesson 2 (should succeed)
        response = self.client.patch(f'/api/progress/{progress2.id}/', {
            'completed': True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Complete lesson 3 (should succeed)
        response = self.client.patch(f'/api/progress/{progress3.id}/', {
            'completed': True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_completion_endpoint_enforces_sequential_order(self):
        # The complete endpoint should enforce sequential order
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course
        )
        
        progress1 = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=self.lesson1,
            completed=False
        )
        progress2 = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=self.lesson2,
            completed=False
        )
        
        # Try to complete lesson 2 using complete endpoint (should fail)
        response = self.client.post(f'/api/progress/{progress2.id}/complete/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Complete lesson 1 (should succeed)
        response = self.client.post(f'/api/progress/{progress1.id}/complete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Now complete lesson 2 (should succeed)
        response = self.client.post(f'/api/progress/{progress2.id}/complete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_progress_information_calculation(self):
        # Progress information should be calculated correctly
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course
        )
        
        # Create progress records
        progress1 = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=self.lesson1,
            completed=True,
            completed_at=timezone.now()
        )
        progress2 = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=self.lesson2,
            completed=False
        )
        progress3 = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=self.lesson3,
            completed=False
        )
        
        response = self.client.get(f'/api/enrollments/{enrollment.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_lessons'], 3)
        self.assertEqual(response.data['completed_lessons'], 1)
        self.assertEqual(response.data['completion_percentage'], 33.33)
        self.assertFalse(response.data['is_completed'])


class AsyncTaskTriggeringTestCase(TestCase):

    def setUp(self):
        # Set up test data
        self.instructor = User.objects.create_user(
            email='instructor@test.com',
            password='testpass123',
            full_name='Test Instructor',
            role=Role.INSTRUCTOR
        )
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            full_name='Test Student',
            role=Role.STUDENT
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            short_description='Test',
            instructor=self.instructor,
            status='published'
        )
        
        self.lesson1 = Lesson.objects.create(
            course=self.course,
            title='Lesson 1',
            content='Content 1',
            order=1
        )
        self.lesson2 = Lesson.objects.create(
            course=self.course,
            title='Lesson 2',
            content='Content 2',
            order=2
        )
    
    @patch('apps.courses.tasks.send_course_completion_notification.delay')
    def test_course_completion_triggers_async_task(self, mock_task):
        # Completing all lessons should trigger async task
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course
        )
        
        progress1 = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=self.lesson1,
            completed=False
        )
        progress2 = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=self.lesson2,
            completed=False
        )
        
        # Complete first lesson
        progress1.completed = True
        progress1.completed_at = timezone.now()
        progress1.save()
        
        # Task should not be triggered yet
        mock_task.assert_not_called()
        
        # Complete second lesson (all lessons done)
        progress2.completed = True
        progress2.completed_at = timezone.now()
        progress2.save()
        
        # Manually trigger the completion check (simulating view behavior)
        from apps.courses.views import LessonProgressViewSet
        viewset = LessonProgressViewSet()
        viewset._check_course_completion(enrollment)
        
        # Task should be triggered with enrollment ID
        mock_task.assert_called_once_with(enrollment.id)
        
        # Enrollment should be marked as completed
        enrollment.refresh_from_db()
        self.assertIsNotNone(enrollment.completed_at)
    
    @patch('apps.courses.tasks.send_course_completion_notification.delay')
    def test_partial_completion_does_not_trigger_task(self, mock_task):
        # Partial completion should not trigger async task
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course
        )
        
        progress1 = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=self.lesson1,
            completed=False
        )
        progress2 = LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=self.lesson2,
            completed=False
        )
        
        # Complete only first lesson
        progress1.completed = True
        progress1.completed_at = timezone.now()
        progress1.save()
        
        # Check completion (should not trigger)
        from apps.courses.views import LessonProgressViewSet
        viewset = LessonProgressViewSet()
        viewset._check_course_completion(enrollment)
        
        # Task should not be triggered
        mock_task.assert_not_called()
        
        # Enrollment should not be marked as completed
        enrollment.refresh_from_db()
        self.assertIsNone(enrollment.completed_at)
    
    def test_task_handles_missing_enrollment_gracefully(self):
        # Task should handle missing enrollment gracefully
        from apps.courses.tasks import send_course_completion_notification
        
        # Call task with non-existent enrollment ID
        result = send_course_completion_notification(99999)
        
        # Should return error message, not raise exception
        self.assertIn('not found', result.lower())
    
    @patch('apps.courses.tasks.send_mail')
    def test_task_sends_notification_correctly(self, mock_send_mail):
        # Task should send notification with correct details
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course
        )
        
        from apps.courses.tasks import send_course_completion_notification
        
        result = send_course_completion_notification(enrollment.id)
        
        # Verify email was sent
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        
        # Check email content
        self.assertIn(self.course.title, call_args.kwargs['subject'])
        self.assertIn(self.student.email, call_args.kwargs['recipient_list'])
        self.assertIn(self.student.full_name, call_args.kwargs['message'])
        
        # Check result
        self.assertIn('sent', result.lower())


class LessonOrderTestCase(APITestCase):
    def setUp(self):
        # Set up test data
        self.instructor = User.objects.create_user(
            email='instructor@test.com',
            password='testpass123',
            full_name='Test Instructor',
            role=Role.INSTRUCTOR
        )
        self.instructor_token = RefreshToken.for_user(self.instructor)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.instructor_token.access_token}')
        
        self.course = Course.objects.create(
            title='Test Course',
            short_description='Test',
            instructor=self.instructor,
            status='draft'
        )
    
    def test_lessons_ordered_correctly(self):
        # Lessons should be returned in correct order
        Lesson.objects.create(course=self.course, title='Lesson 3', content='Content', order=3)
        Lesson.objects.create(course=self.course, title='Lesson 1', content='Content', order=1)
        Lesson.objects.create(course=self.course, title='Lesson 2', content='Content', order=2)
        
        response = self.client.get(f'/api/lessons/?course={self.course.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        orders = [lesson['order'] for lesson in response.data['results']]
        self.assertEqual(orders, [1, 2, 3])
    
    def test_bulk_create_lessons(self):
        # Should be able to create multiple lessons at once
        response = self.client.post('/api/lessons/bulk_create/', {
            'course': self.course.id,
            'lessons': [
                {'title': 'Lesson 1', 'content': 'Content 1', 'order': 1},
                {'title': 'Lesson 2', 'content': 'Content 2', 'order': 2},
                {'title': 'Lesson 3', 'content': 'Content 3', 'order': 3}
            ]
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 3)
        
        # Verify lessons were created
        lesson_count = Lesson.objects.filter(course=self.course).count()
        self.assertEqual(lesson_count, 3)
