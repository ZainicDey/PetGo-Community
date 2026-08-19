# API Testing Patterns

> Comprehensive testing strategies including mock services, contract testing, and integration with popular testing frameworks.

## Testing Strategy

### Test Pyramid

```
          /\
         /E2E\          Few, expensive, slow
        /------\
       /Integration\    Some, moderate cost
      /--------------\
     /     Unit       \  Many, cheap, fast
    /------------------\
```

### Coverage Targets

| Layer | Target | Focus |
|:------|:-------|:------|
| Unit | 80%+ | Business logic, utilities |
| Integration | 60%+ | API endpoints, database |
| E2E | Critical paths | User journeys |
| Contract | 100% | API specification compliance |

---

## Mock Server Framework

### FastAPI-based Mock Server

```python
from fastapi import FastAPI, Request, Response
from typing import Dict, Any
import json

class MockServer:
    def __init__(self):
        self.app = FastAPI(title="Mock API Server")
        self.stubs: Dict[str, Dict] = {}
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
        async def handle_request(path: str, request: Request):
            key = f"{request.method}:/{path}"
            
            if key not in self.stubs:
                return Response(
                    content=json.dumps({"error": "No stub found"}),
                    status_code=404
                )
            
            stub = self.stubs[key]
            return Response(
                content=json.dumps(stub["response"]["body"]),
                status_code=stub["response"].get("status", 200),
                headers=stub["response"].get("headers", {})
            )
    
    def add_stub(self, method: str, path: str, response: Dict):
        key = f"{method}:{path}"
        self.stubs[key] = {"response": response}
    
    def reset(self):
        self.stubs.clear()
```

### Usage Example

```python
mock = MockServer()

# Add stubs
mock.add_stub("GET", "/api/users/123", {
    "body": {"id": "123", "name": "Test User"},
    "status": 200
})

mock.add_stub("POST", "/api/users", {
    "body": {"id": "456", "name": "New User"},
    "status": 201
})

# Run server
import uvicorn
uvicorn.run(mock.app, port=3001)
```

---

## Scenario-Based Testing

### Happy Path Scenario

```python
HAPPY_PATH = {
    "name": "happy_path",
    "description": "All operations succeed",
    "stubs": [
        {
            "method": "POST",
            "path": "/api/auth/login",
            "response": {
                "status": 200,
                "body": {
                    "token": "valid_jwt_token",
                    "user": {"id": "123", "name": "Test User"}
                }
            }
        },
        {
            "method": "GET",
            "path": "/api/users/123",
            "response": {
                "status": 200,
                "body": {"id": "123", "name": "Test User", "email": "test@example.com"}
            }
        }
    ]
}
```

### Error Scenario

```python
ERROR_SCENARIO = {
    "name": "error_conditions",
    "description": "Various error conditions",
    "stubs": [
        {
            "method": "POST",
            "path": "/api/auth/login",
            "conditions": [
                {
                    "match": {"body": {"username": "locked_user"}},
                    "response": {"status": 423, "body": {"error": "Account locked"}}
                },
                {
                    "match": {"body": {"password": "wrong"}},
                    "response": {"status": 401, "body": {"error": "Invalid credentials"}}
                }
            ]
        }
    ]
}
```

### Rate Limiting Scenario

```python
RATE_LIMIT_SCENARIO = {
    "name": "rate_limiting",
    "sequence": [
        {"repeat": 5, "response": {"status": 200, "body": {"ok": True}}},
        {"repeat": 10, "response": {"status": 429, "body": {"error": "Rate limit exceeded"}}}
    ]
}
```

---

## Contract Testing

### OpenAPI Validation

```python
from openapi_spec_validator import validate_spec
from jsonschema import validate, ValidationError

class ContractValidator:
    def __init__(self, spec_path: str):
        with open(spec_path) as f:
            self.spec = yaml.safe_load(f)
        validate_spec(self.spec)
    
    def validate_response(self, path: str, method: str, status: int, body: dict):
        """Validate response against OpenAPI spec."""
        endpoint = self.spec["paths"].get(path, {}).get(method.lower())
        if not endpoint:
            raise ValueError(f"Endpoint {method} {path} not found in spec")
        
        response_spec = endpoint["responses"].get(str(status))
        if not response_spec:
            raise ValueError(f"Status {status} not defined for {method} {path}")
        
        schema = response_spec.get("content", {}).get("application/json", {}).get("schema")
        if schema:
            try:
                validate(instance=body, schema=schema)
            except ValidationError as e:
                raise AssertionError(f"Response doesn't match schema: {e.message}")
```

### Pact Contract Testing

```python
# Consumer test
from pact import Consumer, Provider

pact = Consumer('frontend').has_pact_with(Provider('backend'))

def test_get_user():
    expected = {"id": "123", "name": "Test User"}
    
    (pact
     .given("user 123 exists")
     .upon_receiving("a request for user 123")
     .with_request("GET", "/api/users/123")
     .will_respond_with(200, body=expected))
    
    with pact:
        response = requests.get(f"{pact.uri}/api/users/123")
        assert response.json() == expected
```

---

## pytest Integration

### Fixtures

```python
# conftest.py
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

@pytest.fixture
def mock_external_api(mocker):
    """Mock external API calls."""
    mock = AsyncMock()
    mock.return_value = {"status": "ok"}
    mocker.patch("app.services.external_api.call", mock)
    return mock

@pytest.fixture
async def client():
    """Async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def auth_headers(user_factory):
    """Generate auth headers for testing."""
    user = user_factory()
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}
```

### Test Examples

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestUserAPI:
    async def test_create_user_success(self, client: AsyncClient):
        response = await client.post("/api/users", json={
            "email": "new@example.com",
            "password": "SecurePass123!"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert "id" in data
        assert "password" not in data
    
    async def test_create_user_duplicate_email(self, client: AsyncClient, user_factory):
        user_factory(email="existing@example.com")
        
        response = await client.post("/api/users", json={
            "email": "existing@example.com",
            "password": "SecurePass123!"
        })
        
        assert response.status_code == 400
        assert "already exists" in response.json()["message"]
    
    async def test_get_user_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/users/123")
        
        assert response.status_code == 401
    
    async def test_get_user_success(self, client: AsyncClient, auth_headers, user_factory):
        user = user_factory()
        
        response = await client.get(
            f"/api/users/{user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["id"] == str(user.id)
```

---

## Dynamic Data Generation

### Faker Integration

```python
from faker import Faker

fake = Faker()

def generate_user():
    return {
        "id": fake.uuid4(),
        "email": fake.email(),
        "name": fake.name(),
        "created_at": fake.iso8601()
    }

def generate_product():
    return {
        "id": fake.uuid4(),
        "name": fake.catch_phrase(),
        "price": round(fake.pyfloat(min_value=1, max_value=999), 2),
        "category": fake.random_element(["electronics", "clothing", "books"]),
        "in_stock": fake.boolean()
    }
```

### Factory Pattern

```python
import factory
from factory.alchemy import SQLAlchemyModelFactory

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session
    
    email = factory.LazyAttribute(lambda _: fake.email())
    name = factory.LazyAttribute(lambda _: fake.name())
    is_active = True
    
    @factory.post_generation
    def groups(self, create, extracted):
        if extracted:
            for group in extracted:
                self.groups.append(group)

# Usage
user = UserFactory()
admin = UserFactory(groups=[admin_group])
```

---

## Performance Testing

### Load Test Configuration

```python
LOAD_TEST_SCENARIOS = {
    "gradual_load": {
        "stages": [
            {"duration": 60, "target_rps": 100},
            {"duration": 120, "target_rps": 500},
            {"duration": 180, "target_rps": 1000},
            {"duration": 60, "target_rps": 100}
        ]
    },
    "spike_test": {
        "stages": [
            {"duration": 60, "target_rps": 100},
            {"duration": 10, "target_rps": 5000},
            {"duration": 60, "target_rps": 100}
        ]
    },
    "stress_test": {
        "stages": [
            {"duration": 60, "target_rps": 100},
            {"duration": 60, "target_rps": 500},
            {"duration": 60, "target_rps": 1000},
            {"duration": 60, "target_rps": 2000},
            {"duration": 60, "target_rps": 5000}
        ]
    }
}
```

### Locust Example

```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get token
        response = self.client.post("/api/auth/login", json={
            "username": "test@example.com",
            "password": "password123"
        })
        self.token = response.json()["token"]
    
    @task(3)
    def get_users(self):
        self.client.get("/api/users", headers={
            "Authorization": f"Bearer {self.token}"
        })
    
    @task(1)
    def create_user(self):
        self.client.post("/api/users", json={
            "email": f"user{random.randint(1, 10000)}@example.com",
            "name": "Load Test User"
        }, headers={
            "Authorization": f"Bearer {self.token}"
        })
```
