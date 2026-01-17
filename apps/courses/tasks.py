from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from apps.courses.models.enrollment import Enrollment
import logging


@shared_task
def send_course_completion_notification(enrollment_id):
    try:
        enrollment = Enrollment.objects.select_related('student', 'course').get(id=enrollment_id)
        student = enrollment.student
        course = enrollment.course
        
        subject = f'Congratulations! You completed {course.title}'
        message = f"""
        Dear {student.full_name},
        
        Congratulations! You have successfully completed the course "{course.title}".
        
        We hope you enjoyed the course and learned valuable skills.
        
        Best regards,
        Course Platform Team
        """
        
       
        logging.info(f"Sending completion notification to {student.email} for course {course.title}")
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.email],
            fail_silently=False,
        )
        
        return f"Notification sent to {student.email} for course completion"
    except Enrollment.DoesNotExist:
        return f"Enrollment with id {enrollment_id} not found"
    except Exception as e:
        return f"Error sending notification: {str(e)}"
