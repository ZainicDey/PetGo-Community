---
name: api-builder
description: Use when building REST/GraphQL APIs with Python (FastAPI or Django). For API design, authentication, documentation, testing, mock services, observability, and production deployment.
---

# API Builder

End-to-end Python API development guide: from design to production deployment.

## 🎯 Overview

This skill provides comprehensive guidance for building production-grade APIs with:
- **FastAPI** - High-performance async-first APIs with Pydantic V2
- **Django** - Enterprise-grade apps with DRF and "batteries included"
- **API Documentation** - OpenAPI 3.1, SDKs, and developer portals
- **Mock Services** - Parallel development and comprehensive testing
- **Observability** - Logs, traces, metrics, and health checks

---

## 📋 Quick Start: Framework Selection

```markdown
Choose your framework based on project needs:

| Criteria | FastAPI | Django |
|:---------|:--------|:-------|
| **Primary Use** | High-concurrency APIs | Full-featured web apps |
| **Async Support** | Native, first-class | Available (Django 5.x) |
| **ORM** | SQLAlchemy 2.0 | Django ORM |
| **Learning Curve** | Low (Python hints) | Medium (conventions) |
| **Admin Panel** | Manual setup | Built-in |
| **Best For** | Microservices, ML APIs | SaaS, E-commerce |
```

---

## 🔧 Framework-Specific Guides

### FastAPI Development
- Async/await patterns for high-concurrency
- Pydantic V2 for data validation
- SQLAlchemy 2.0 async with asyncpg
- Background tasks and task queues
- **[📖 Full Guide: references/fastapi-patterns.md](references/fastapi-patterns.md)**

### Django Development
- Django 5.x async views and middleware
- ORM optimization (select_related, prefetch_related)
- Django REST Framework (DRF) patterns
- Celery for background tasks
- **[📖 Full Guide: references/django-patterns.md](references/django-patterns.md)**

---

## 🔐 Authentication & Security

### Supported Patterns
| Pattern | FastAPI | Django |
|:--------|:--------|:-------|
| JWT Tokens | python-jose, pyjwt | djangorestframework-simplejwt |
| OAuth2/OIDC | authlib, python-social-auth | django-allauth |
| API Keys | Custom middleware | DRF TokenAuth |
| RBAC | Custom decorators | django-guardian |

### Security Checklist
```markdown
- [ ] CORS properly configured
- [ ] CSRF protection enabled (Django)
- [ ] Input sanitization on all endpoints
- [ ] Rate limiting per user/IP
- [ ] SQL injection prevention (parameterized queries)
- [ ] Security headers (CSP, HSTS, X-Frame-Options)
```

**[📖 Full Guide: references/security-patterns.md](references/security-patterns.md)**

---

## 📚 API Documentation

### OpenAPI 3.1 Best Practices
1. **Design-First**: Write spec before implementation
2. **Rich Examples**: Include request/response samples
3. **Error Documentation**: Document all error codes
4. **Authentication Flows**: Visual guides for OAuth2

### Documentation Tools
| Tool | Purpose |
|:-----|:--------|
| Swagger UI | Interactive API explorer |
| Redoc | Beautiful static docs |
| Stoplight Studio | Collaborative design |
| Mintlify/ReadMe | AI-powered docs |

**[📖 Full Guide: references/documentation-patterns.md](references/documentation-patterns.md)**

---

## 🧪 Testing & Mocking

### Testing Strategy
```markdown
1. **Unit Tests** - Service layer logic
2. **Integration Tests** - Database + API endpoints
3. **Contract Tests** - OpenAPI spec validation
4. **E2E Tests** - Full user flows
```

### Mock Server Capabilities
- Dynamic stubbing with request matching
- Scenario-based testing (happy path, errors, slow)
- Faker-powered realistic data generation
- pytest/Jest integration

**[📖 Full Guide: references/testing-patterns.md](references/testing-patterns.md)**

---

## 📊 Observability

### Three Pillars
| Pillar | Tools |
|:-------|:------|
| **Logs** | structlog, loguru |
| **Traces** | OpenTelemetry, Jaeger |
| **Metrics** | Prometheus, Grafana |

### Required Endpoints
```python
# Health check (required)
GET /health       # → {"status": "healthy"}
GET /health/ready # → {"database": "ok", "redis": "ok"}
GET /health/live  # → {"pid": 12345}

# Metrics (Prometheus format)
GET /metrics      # → prometheus_client output
```

**[📖 Full Guide: references/observability-patterns.md](references/observability-patterns.md)**

---

## 🚀 Deployment

### Production Checklist
```markdown
- [ ] Docker multi-stage build
- [ ] Environment-based config (12-factor)
- [ ] Uvicorn/Gunicorn with workers
- [ ] Database connection pooling
- [ ] Static files served via CDN
- [ ] SSL termination at load balancer
- [ ] Health checks for orchestrator
```

### Deployment Targets
| Target | Config |
|:-------|:-------|
| Docker | Dockerfile + docker-compose |
| Kubernetes | Helm charts + HPA |
| Serverless | AWS Lambda + API Gateway |

**[📖 Full Guide: references/deployment-patterns.md](references/deployment-patterns.md)**

---

## 🛠️ Project Templates

### FastAPI Microservice
```bash
project/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   └── router.py
│   │   └── deps.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   ├── schemas/
│   └── services/
├── tests/
├── alembic/
└── docker-compose.yml
```

### Django REST API
```bash
project/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   └── urls.py
├── apps/
│   ├── users/
│   ├── core/
│   └── api/
├── tests/
└── docker-compose.yml
```

---

## 📚 Core Principles

1. **API-First Design** - Write OpenAPI spec before code
2. **Type Safety** - Pydantic/Django serializers everywhere
3. **Async Where Needed** - I/O bound = async, CPU bound = sync
4. **Test Pyramid** - Many unit, some integration, few E2E
5. **Observability by Default** - Logs, traces, metrics from day 1
6. **Security First** - Auth, validation, rate limiting always
7. **Documentation as Code** - Keep docs in sync with API
8. **12-Factor Config** - Environment-based configuration
