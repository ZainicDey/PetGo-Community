# Django Development Patterns

> Expert guidance for Django 5.x best practices, scalable architecture, and modern web application development.

## Core Django Expertise

### Modern Django Features
- Django 5.x async views, middleware, and ORM operations
- Model design with proper relationships, indexes, and optimization
- Class-based views (CBVs) and function-based views (FBVs)
- Django ORM optimization with select_related, prefetch_related
- Custom model managers, querysets, and database functions
- Django signals and their proper usage patterns
- Django admin customization and ModelAdmin configuration

---

## Project Structure

```bash
project/
├── config/
│   ├── settings/
│   │   ├── base.py         # Shared settings
│   │   ├── local.py        # Development
│   │   ├── production.py   # Production
│   │   └── test.py         # Testing
│   ├── urls.py
│   └── wsgi.py / asgi.py
├── apps/
│   ├── users/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── services.py     # Business logic
│   ├── core/               # Shared utilities
│   └── api/                # API configuration
├── tests/
│   ├── conftest.py
│   └── apps/
└── manage.py
```

---

## Django REST Framework (DRF)

### ViewSet Pattern

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optimize with select_related for foreign keys."""
        return User.objects.select_related(
            'profile'
        ).prefetch_related(
            'groups', 'permissions'
        )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Custom action: POST /users/{id}/activate/"""
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({'status': 'activated'})
```

### Serializer Patterns

```python
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'profile', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value.lower()
```

---

## ORM Optimization

### Avoiding N+1 Queries

```python
# ❌ Bad: N+1 queries
users = User.objects.all()
for user in users:
    print(user.profile.bio)  # Extra query per user

# ✅ Good: Single query with join
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.bio)  # No extra queries

# ✅ Good: Prefetch for many-to-many
users = User.objects.prefetch_related('groups').all()
for user in users:
    print([g.name for g in user.groups.all()])  # No extra queries
```

### Custom QuerySet Methods

```python
class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status='published', published_at__lte=timezone.now())
    
    def by_author(self, user):
        return self.filter(author=user)
    
    def with_stats(self):
        return self.annotate(
            view_count=Count('views'),
            comment_count=Count('comments')
        )

class ArticleManager(models.Manager):
    def get_queryset(self):
        return ArticleQuerySet(self.model, using=self._db)
    
    def published(self):
        return self.get_queryset().published()

class Article(models.Model):
    # ... fields ...
    objects = ArticleManager()
```

---

## Async Django (5.x)

### Async Views

```python
from django.http import JsonResponse
from asgiref.sync import sync_to_async

async def async_user_list(request):
    """Async view with database access."""
    users = await sync_to_async(list)(
        User.objects.values('id', 'email')[:100]
    )
    return JsonResponse({'users': users})

# With async ORM (Django 5.x)
async def async_user_detail(request, user_id):
    try:
        user = await User.objects.aget(id=user_id)
        return JsonResponse({
            'id': user.id,
            'email': user.email
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
```

### Async DRF Views

```python
from adrf.views import APIView  # django-rest-framework-async

class AsyncUserView(APIView):
    async def get(self, request):
        users = [u async for u in User.objects.all()[:100]]
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
```

---

## Celery Integration

### Configuration

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# settings/base.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_ALWAYS_EAGER = False  # True for testing
CELERY_TASK_SERIALIZER = 'json'
```

### Task Definition

```python
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def send_email_task(self, user_id, subject, body):
    try:
        user = User.objects.get(id=user_id)
        send_mail(subject, body, 'noreply@example.com', [user.email])
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

# Usage
send_email_task.delay(user.id, "Welcome!", "Thanks for signing up")
```

---

## Authentication

### JWT with Simple JWT

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# urls.py
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
]
```

---

## Testing

### pytest-django Setup

```python
# conftest.py
import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user_factory):
    user = user_factory()
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def user_factory(db):
    def create_user(**kwargs):
        return User.objects.create_user(
            email=kwargs.get('email', 'test@example.com'),
            password=kwargs.get('password', 'testpass123')
        )
    return create_user
```

### Test Examples

```python
@pytest.mark.django_db
class TestUserAPI:
    def test_list_users(self, authenticated_client, user_factory):
        user_factory(email='user1@example.com')
        user_factory(email='user2@example.com')
        
        response = authenticated_client.get('/api/users/')
        
        assert response.status_code == 200
        assert len(response.json()) >= 2
    
    def test_create_user(self, api_client):
        response = api_client.post('/api/users/', {
            'email': 'new@example.com',
            'password': 'secure123'
        })
        
        assert response.status_code == 201
        assert User.objects.filter(email='new@example.com').exists()
```

---

## Deployment

### ASGI Configuration

```python
# config/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

### Production Settings

```python
# settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
    }
}

# Database
DATABASES['default']['CONN_MAX_AGE'] = 600
```
