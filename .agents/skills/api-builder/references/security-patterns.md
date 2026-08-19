# API Security Patterns

> Comprehensive security patterns for authentication, authorization, and API protection.

## Authentication Patterns

### JWT Token Flow

```
┌─────────┐           ┌─────────┐           ┌─────────┐
│  Client │           │   API   │           │   DB    │
└────┬────┘           └────┬────┘           └────┬────┘
     │    POST /login      │                     │
     │────────────────────>│    Verify user      │
     │                     │────────────────────>│
     │                     │    User data        │
     │                     │<────────────────────│
     │  { access, refresh }│                     │
     │<────────────────────│                     │
     │                     │                     │
     │  GET /api (+ token) │                     │
     │────────────────────>│                     │
     │    Protected data   │                     │
     │<────────────────────│                     │
```

### Token Configuration

```python
# Production-ready JWT settings
JWT_CONFIG = {
    "ACCESS_TOKEN_LIFETIME": 15,      # minutes
    "REFRESH_TOKEN_LIFETIME": 7,       # days
    "ALGORITHM": "HS256",              # or RS256 for asymmetric
    "ISSUER": "api.example.com",
    "AUDIENCE": "example.com",
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_ENABLED": True,
}
```

### Refresh Token Strategy

```python
from datetime import datetime, timedelta
from jose import jwt
from redis import Redis

redis = Redis()

def create_tokens(user_id: str) -> dict:
    """Create access and refresh tokens."""
    access_token = jwt.encode(
        {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(minutes=15),
            "type": "access"
        },
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    
    refresh_token = jwt.encode(
        {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(days=7),
            "type": "refresh",
            "jti": str(uuid.uuid4())  # Unique token ID
        },
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    
    return {"access_token": access_token, "refresh_token": refresh_token}

def blacklist_token(jti: str, exp: datetime):
    """Add token to blacklist."""
    ttl = int((exp - datetime.utcnow()).total_seconds())
    redis.setex(f"blacklist:{jti}", ttl, "1")

def is_token_blacklisted(jti: str) -> bool:
    """Check if token is blacklisted."""
    return redis.exists(f"blacklist:{jti}") > 0
```

---

## Authorization Patterns

### Role-Based Access Control (RBAC)

```python
from enum import Enum
from functools import wraps
from fastapi import HTTPException, status

class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"

class Permission(str, Enum):
    READ_USERS = "users:read"
    WRITE_USERS = "users:write"
    DELETE_USERS = "users:delete"
    READ_REPORTS = "reports:read"

ROLE_PERMISSIONS = {
    Role.ADMIN: [Permission.READ_USERS, Permission.WRITE_USERS, Permission.DELETE_USERS, Permission.READ_REPORTS],
    Role.MANAGER: [Permission.READ_USERS, Permission.WRITE_USERS, Permission.READ_REPORTS],
    Role.USER: [Permission.READ_USERS],
}

def require_permission(permission: Permission):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value} required"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage
@router.delete("/users/{user_id}")
@require_permission(Permission.DELETE_USERS)
async def delete_user(user_id: int, current_user: User = Depends(get_current_user)):
    ...
```

### Resource-Level Authorization

```python
from fastapi import HTTPException, Depends

class ResourceAuthorizer:
    async def authorize(
        self, 
        resource_id: int, 
        user: User, 
        action: str
    ) -> bool:
        """Check if user can perform action on resource."""
        resource = await self.get_resource(resource_id)
        
        # Owner can do anything
        if resource.owner_id == user.id:
            return True
        
        # Check shared permissions
        permission = await Permission.objects.filter(
            resource_id=resource_id,
            user_id=user.id,
            action=action
        ).first()
        
        return permission is not None

def require_resource_access(action: str):
    async def dependency(
        resource_id: int,
        user: User = Depends(get_current_user),
        authorizer: ResourceAuthorizer = Depends()
    ):
        if not await authorizer.authorize(resource_id, user, action):
            raise HTTPException(status_code=403, detail="Access denied")
        return True
    return Depends(dependency)

# Usage
@router.put("/documents/{doc_id}")
async def update_document(
    doc_id: int,
    data: DocumentUpdate,
    _: bool = require_resource_access("write")
):
    ...
```

---

## Rate Limiting

### Token Bucket Implementation

```python
from fastapi import Request, HTTPException
import time
from redis import Redis

redis = Redis()

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rate = requests_per_minute
        self.window = 60  # seconds
    
    async def check_rate_limit(self, key: str) -> bool:
        """Check and update rate limit."""
        current_time = int(time.time())
        window_start = current_time - self.window
        
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, self.window)
        
        results = pipe.execute()
        request_count = results[1]
        
        return request_count < self.rate

async def rate_limit_dependency(
    request: Request,
    limiter: RateLimiter = Depends()
):
    # Use IP or user ID as key
    key = f"rate_limit:{request.client.host}"
    
    if not await limiter.check_rate_limit(key):
        raise HTTPException(
            status_code=429,
            detail="Too many requests",
            headers={"Retry-After": "60"}
        )
```

### Tiered Rate Limits

```python
RATE_LIMITS = {
    "free": {"requests_per_minute": 60, "requests_per_day": 1000},
    "basic": {"requests_per_minute": 300, "requests_per_day": 10000},
    "pro": {"requests_per_minute": 1000, "requests_per_day": 100000},
}

async def get_user_rate_limit(user: User) -> dict:
    return RATE_LIMITS.get(user.plan, RATE_LIMITS["free"])
```

---

## Input Validation & Sanitization

### Pydantic Validation

```python
from pydantic import BaseModel, EmailStr, field_validator, Field
import re

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    username: str = Field(..., min_length=3, max_length=50)
    
    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain special character")
        return v
    
    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username must be alphanumeric")
        return v
```

### SQL Injection Prevention

```python
# ❌ NEVER - String interpolation
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ ALWAYS - Parameterized queries
# SQLAlchemy
result = await session.execute(
    select(User).where(User.id == user_id)
)

# Raw SQL with parameters
result = await session.execute(
    text("SELECT * FROM users WHERE id = :id"),
    {"id": user_id}
)
```

---

## Security Headers

### FastAPI Middleware

```python
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        
        return response

app = FastAPI()
app.add_middleware(SecurityHeadersMiddleware)
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

# Production CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,  # Cache preflight for 10 minutes
)

# ❌ NEVER in production
# allow_origins=["*"]
```

---

## API Key Security

### Secure API Key Storage

```python
import hashlib
import secrets

def generate_api_key() -> tuple[str, str]:
    """Generate API key and its hash."""
    # Prefix for easy identification
    prefix = "sk_live_"
    key = prefix + secrets.token_urlsafe(32)
    
    # Store only the hash
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    
    return key, key_hash

def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    """Verify API key against stored hash."""
    provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
    return secrets.compare_digest(provided_hash, stored_hash)
```

### API Key Middleware

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(
    api_key: str = Security(api_key_header)
) -> APIKey:
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    api_key_obj = await APIKey.objects.filter(
        key_hash=key_hash,
        is_active=True
    ).first()
    
    if not api_key_obj:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # Update last used timestamp
    await api_key_obj.update(last_used_at=datetime.utcnow())
    
    return api_key_obj
```

---

## Security Checklist

```markdown
## Authentication
- [ ] Use strong password hashing (bcrypt, argon2)
- [ ] Implement account lockout after failed attempts
- [ ] Use secure session management
- [ ] Implement MFA for sensitive operations

## Authorization
- [ ] Validate permissions on every request
- [ ] Implement resource-level access control
- [ ] Use principle of least privilege
- [ ] Log all authorization failures

## Data Protection
- [ ] Encrypt sensitive data at rest
- [ ] Use TLS 1.3 for all connections
- [ ] Never log sensitive data
- [ ] Implement data retention policies

## API Security
- [ ] Rate limit all endpoints
- [ ] Validate and sanitize all input
- [ ] Use parameterized queries
- [ ] Implement request size limits

## Infrastructure
- [ ] Use security headers
- [ ] Configure CORS properly
- [ ] Keep dependencies updated
- [ ] Regular security audits
```
