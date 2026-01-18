# Course Platform Backend

A Django REST Framework-based course platform that allows instructors to create courses and lessons, and students to enroll, complete lessons, and track progress.

## Tech Stack

- **Django 6.0.1** - Web framework
- **Django REST Framework** - API framework
- **PostgreSQL** - Database
- **Celery** - Asynchronous task queue
- **Redis** - Message broker for Celery
- **JWT Authentication** - Token-based authentication

## Features

### User Management
- Role-based users (Student/Instructor)
- JWT-based authentication
- User registration

### Course Management
- Instructors can create and manage courses
- Courses start in draft state
- Only published courses are visible to students
- Instructors can only manage their own courses

### Lesson Management
- Ordered lessons within courses
- Instructors can add lessons to their courses

### Enrollment & Progress Tracking
- Students can enroll in published courses
- Track progress through individual lessons
- Automatic course completion detection
- Async notification when course is completed

## Setup Instructions

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend-developer-assignment-OLE
   ```

2. **Build and start containers**
   ```bash
   docker compose up --build
   ```

   This will start:
   - PostgreSQL database (port 5432)
   - Redis (port 6379)
   - Django web server (port 8000)
   - Celery worker

3. **Create a superuser** (in a new terminal)
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

## Common Test Commands

```bash
# Quick test run (all tests, minimal output)
python manage.py test

# Detailed test run (verbose output)
python manage.py test --verbosity=2

# Run specific app tests with details
python manage.py test apps.courses --verbosity=2

# Run tests and keep database
python manage.py test --keepdb --verbosity=2

# Run only authorization tests
python manage.py test apps.courses.tests.AuthorizationBoundaryTestCase --verbosity=2

# Run only enrollment logic tests
python manage.py test apps.courses.tests.EnrollmentLogicTestCase --verbosity=2

# Run only async task tests
python manage.py test apps.courses.tests.AsyncTaskTriggeringTestCase --verbosity=2
``` 

### Manual Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL database**
   - Create a database named `course_platform`
   - Update database credentials in `core/settings.py` or use environment variables

3. **Set environment variables** 
   ```bash
   DB_NAME=course_platform
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=localhost
   DB_PORT=5432
   
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_USE_TLS = True
   EMAIL_HOST = 'smtp.mailtrap.io'
   EMAIL_PORT = 2525
   EMAIL_HOST_USER = 'your_email@example.com'
   EMAIL_HOST_PASSWORD = 'your_email_password'
   DEFAULT_FROM_EMAIL = 'your_email@example.com'

   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start Redis** (required for Celery)
   ```bash
   redis-server
   ```

7. **Start Celery worker** (in a new terminal)
   ```bash
   celery -A core worker -l info
   ```

8. **Start development server**
   ```bash
   python manage.py runserver
   ```

### Using docker-compose run (one-off container)

```bash
# Run tests in a new container
docker compose run --rm web python manage.py test

# With verbose output
docker compose run --rm web python manage.py test --verbosity=2
```


## API Documentation

The API documentation is available via Swagger UI and ReDoc (powered by drf-spectacular):

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/redoc/
- **OpenAPI Schema (JSON)**: http://localhost:8000/api/schema/

### Authentication in Swagger

To use authenticated endpoints in Swagger:
1. First, obtain a JWT token by using the `/api/auth/login/` endpoint
2. Click the "Authorize" button (lock icon) in Swagger UI
3. Enter: `<your_access_token>` 
4. Click "Authorize" and then "Close"
5. The authorization will persist across requests

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Obtain JWT token (login)
- `POST /api/token/refresh/` - Refresh JWT token
- `POST /api/token/verify/` - Verify JWT token
- `POST /api/register/` - Register new user

### Courses
- `GET /api/courses/` - List courses (published for students, own courses for instructors)
- `POST /api/courses/` - Create course (instructors only)
- `GET /api/courses/{id}/` - Get course details
- `PUT /api/courses/{id}/` - Update course (owner only)
- `DELETE /api/courses/{id}/` - Delete course (owner only)
- `POST /api/courses/{id}/publish/` - Publish draft course (owner only)

### Lessons
- `GET /api/lessons/` - List lessons
- `POST /api/lessons/` - Create lesson (instructors only)
- `POST /api/lessons/bulk_create` - Create lesson in bulk (instructors only)
- `GET /api/lessons/{id}/` - Get lesson details
- `PUT /api/lessons/{id}/` - Update lesson (instructors only)
- `DELETE /api/lessons/{id}/` - Delete lesson (instructors only)

### Enrollments
- `GET /api/enrollments/` - List user's enrollments (students only)
- `POST /api/enrollments/` - Enroll in a course (students only)
- `GET /api/enrollments/{id}/` - Get enrollment details with progress information
  - Returns progress data including:
    - `total_lessons`: Total number of lessons in the course
    - `completed_lessons`: Number of completed lessons
    - `completion_percentage`: Percentage of completion (rounded to 2 decimals)
    - `is_completed`: Boolean indicating if enrollment is completed
  - **This is the primary endpoint for students to view their progress for a particular course**

### Progress
- `GET /api/progress/` - List lesson progress (students only)
- `GET /api/progress/{id}/` - Get progress details
- `PUT /api/progress/{id}/` - Update lesson progress (mark as completed)


**Key Components**:
- Celery configuration: `core/celery.py`
- Task definition: `apps/courses/tasks.py`
- Task triggering: `apps/courses/views.py` - `LessonProgressViewSet._check_course_completion()`
- Worker service: Defined in `docker-compose.yml`







## Project Structure

```
backend-developer-assignment-OLE/
├── apps/
│   ├── auth/          # User authentication and management
│   ├── base/          # Base models with common fields
│   └── courses/       # Course, lesson, enrollment, and progress models
├── core/              # Django project settings
├── docker-compose.yml # Docker orchestration
├── Dockerfile         # Docker image definition
└── requirements.txt   # Python dependencies
```

## License

This project is part of a backend developer assignment.
