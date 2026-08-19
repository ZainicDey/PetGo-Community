# API Builder

> End-to-end Python API development guide: from design to production deployment.

## 🚀 Quick Start

```markdown
1. Choose your framework (FastAPI for high-concurrency, Django for full-featured apps)
2. Follow the Quick Start checklist in SKILL.md
3. Reference detailed patterns in references/ for specific topics
```

## ✨ What It Does

API Builder provides comprehensive guidance for building production-grade REST and GraphQL APIs with Python. It covers the entire API lifecycle:

| Phase | Covered Topics |
|:------|:---------------|
| **Design** | Framework selection, project structure, API design patterns |
| **Development** | FastAPI async patterns, Django DRF, Pydantic/Serializers |
| **Security** | JWT/OAuth2, RBAC, rate limiting, input validation |
| **Documentation** | OpenAPI 3.1, SDK generation, developer portals |
| **Testing** | Mock servers, contract testing, pytest integration |
| **Observability** | Structured logging, distributed tracing, Prometheus metrics |
| **Deployment** | Docker, Kubernetes, CI/CD, production configs |

## 🔧 How It Works

The skill is organized with **Progressive Disclosure**:

```
api-builder/
├── SKILL.md              # Overview, quick references, decision matrices
└── references/
    ├── fastapi-patterns.md      # FastAPI deep dive
    ├── django-patterns.md       # Django/DRF deep dive
    ├── documentation-patterns.md # OpenAPI, SDKs, portals
    ├── testing-patterns.md      # Mock servers, contract tests
    ├── security-patterns.md     # Auth, authorization, protection
    ├── observability-patterns.md # Logs, traces, metrics
    └── deployment-patterns.md   # Docker, K8s, CI/CD
```

**SKILL.md** provides quick references and decision frameworks. When you need deeper implementation details, each topic links to its dedicated reference file.

## 🔔 When to Use

Use this skill when you need to:

- **Start a new API project** → Framework selection guide, project templates
- **Implement authentication** → JWT, OAuth2, API keys patterns
- **Write API documentation** → OpenAPI 3.1 best practices, SDK generation
- **Set up testing** → Mock servers, contract testing, pytest fixtures
- **Add observability** → Logging, tracing, metrics, health checks
- **Deploy to production** → Docker configs, Kubernetes manifests, CI/CD

## 📝 Examples

### Example 1: New FastAPI Microservice

```markdown
User: "I need to build a high-performance API for a recommendation engine"

Agent uses: 
- SKILL.md → Framework selection (FastAPI for async/ML)
- references/fastapi-patterns.md → Project structure, async patterns
- references/security-patterns.md → API key authentication
- references/observability-patterns.md → Request tracing
```

### Example 2: Django REST API

```markdown
User: "Building a SaaS backend with user management and billing"

Agent uses:
- SKILL.md → Framework selection (Django for full-featured)
- references/django-patterns.md → DRF viewsets, custom user model
- references/security-patterns.md → JWT with refresh tokens
- references/testing-patterns.md → pytest-django fixtures
```

### Example 3: API Documentation

```markdown
User: "Need to create developer docs for our public API"

Agent uses:
- references/documentation-patterns.md → OpenAPI 3.1 spec
- references/documentation-patterns.md → SDK generation
- references/documentation-patterns.md → Interactive docs setup
```

### Example 4: Production Deployment

```markdown
User: "Ready to deploy our FastAPI service to Kubernetes"

Agent uses:
- references/deployment-patterns.md → Dockerfile multi-stage
- references/deployment-patterns.md → K8s manifests, HPA
- references/observability-patterns.md → Health checks, Prometheus
- references/deployment-patterns.md → GitHub Actions CI/CD
```

## 📚 Reference Files

| File | Topics Covered |
|:-----|:---------------|
| `fastapi-patterns.md` | Async patterns, SQLAlchemy 2.0, Pydantic V2, dependency injection |
| `django-patterns.md` | DRF viewsets, ORM optimization, Celery, Django Channels |
| `documentation-patterns.md` | OpenAPI 3.1, Swagger/Redoc, SDK generation, versioning |
| `testing-patterns.md` | Mock servers, Faker data, contract tests, pytest fixtures |
| `security-patterns.md` | JWT/OAuth2, RBAC, rate limiting, security headers |
| `observability-patterns.md` | structlog, OpenTelemetry, Prometheus, Sentry |
| `deployment-patterns.md` | Docker, Kubernetes, Gunicorn, CI/CD pipelines |

## 🎯 Key Principles

1. **API-First Design** - Write OpenAPI spec before code
2. **Type Safety** - Pydantic/Django serializers everywhere
3. **Async Where Needed** - I/O bound = async, CPU bound = sync
4. **Test Pyramid** - Many unit, some integration, few E2E
5. **Observability by Default** - Logs, traces, metrics from day 1
6. **Security First** - Auth, validation, rate limiting always
7. **Documentation as Code** - Keep docs in sync with API
8. **12-Factor Config** - Environment-based configuration
