# API Documentation Patterns

> Expert guidance for creating world-class developer experiences through comprehensive, interactive, and AI-enhanced API documentation.

## OpenAPI 3.1 Best Practices

### Specification Structure

```yaml
openapi: 3.1.0
info:
  title: My API
  version: 1.0.0
  description: |
    Comprehensive API for managing resources.
    
    ## Authentication
    All endpoints require Bearer token authentication.
    
    ## Rate Limits
    - 100 requests/minute for free tier
    - 1000 requests/minute for paid tier
  contact:
    email: api-support@example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://staging-api.example.com/v1
    description: Staging

security:
  - bearerAuth: []

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

### Endpoint Documentation

```yaml
paths:
  /users/{userId}:
    get:
      operationId: getUserById
      summary: Get user by ID
      description: |
        Retrieves a user's profile including their settings and preferences.
        
        **Permissions Required:** `users:read`
      tags:
        - Users
      parameters:
        - name: userId
          in: path
          required: true
          description: Unique user identifier
          schema:
            type: string
            format: uuid
            example: "550e8400-e29b-41d4-a716-446655440000"
        - name: include
          in: query
          description: Related resources to include
          schema:
            type: array
            items:
              type: string
              enum: [profile, settings, permissions]
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
              example:
                id: "550e8400-e29b-41d4-a716-446655440000"
                email: "user@example.com"
                name: "John Doe"
                createdAt: "2024-01-15T10:30:00Z"
        '404':
          $ref: '#/components/responses/NotFound'
        '401':
          $ref: '#/components/responses/Unauthorized'
```

---

## Documentation Platforms

### Comparison Matrix

| Platform | Pros | Cons | Best For |
|:---------|:-----|:-----|:---------|
| **Swagger UI** | Free, interactive | Basic styling | Internal APIs |
| **Redoc** | Beautiful, responsive | Read-only | Public APIs |
| **Stoplight** | Collaborative, design-first | Learning curve | Team projects |
| **Mintlify** | AI-powered, modern | Paid | Developer portals |
| **ReadMe** | Analytics, versioning | Paid | API products |

### Swagger UI Customization

```html
<!-- Custom Swagger UI with branding -->
<!DOCTYPE html>
<html>
<head>
  <title>API Documentation</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css">
  <style>
    .topbar { background-color: #1a1a2e !important; }
    .info .title { color: #0f4c75; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({
      url: "/openapi.json",
      dom_id: '#swagger-ui',
      presets: [SwaggerUIBundle.presets.apis],
      layout: "BaseLayout",
      tryItOutEnabled: true,
      requestInterceptor: (req) => {
        req.headers['Authorization'] = `Bearer ${localStorage.getItem('token')}`;
        return req;
      }
    });
  </script>
</body>
</html>
```

---

## SDK Generation

### OpenAPI Generator

```bash
# Generate Python SDK
openapi-generator generate \
  -i openapi.yaml \
  -g python \
  -o ./sdks/python \
  --additional-properties=packageName=myapi,projectName=myapi-python

# Generate TypeScript SDK
openapi-generator generate \
  -i openapi.yaml \
  -g typescript-fetch \
  -o ./sdks/typescript \
  --additional-properties=npmName=@myorg/myapi-client
```

### SDK Documentation Template

```markdown
# MyAPI Python SDK

## Installation

\`\`\`bash
pip install myapi-python
\`\`\`

## Quick Start

\`\`\`python
from myapi import Client

client = Client(api_key="your-api-key")

# Get user
user = client.users.get("user-id")
print(user.email)

# Create user
new_user = client.users.create(
    email="new@example.com",
    name="New User"
)
\`\`\`

## Error Handling

\`\`\`python
from myapi.exceptions import NotFoundError, RateLimitError

try:
    user = client.users.get("invalid-id")
except NotFoundError:
    print("User not found")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
\`\`\`
```

---

## Version Management

### Versioning Strategies

| Strategy | URL Format | Pros | Cons |
|:---------|:-----------|:-----|:-----|
| **URL Path** | `/v1/users` | Clear, cacheable | URL pollution |
| **Query Param** | `/users?version=1` | Flexible | Easy to forget |
| **Header** | `Accept-Version: 1` | Clean URLs | Hidden |

### Migration Guide Template

```markdown
# Migrating from API v1 to v2

## Timeline
- v2 Available: January 1, 2025
- v1 Deprecated: March 1, 2025
- v1 Sunset: June 1, 2025

## Breaking Changes

### 1. User Endpoint Response Format

**v1 Response:**
\`\`\`json
{
  "user_id": "123",
  "user_name": "John"
}
\`\`\`

**v2 Response:**
\`\`\`json
{
  "id": "123",
  "name": "John"
}
\`\`\`

### 2. Authentication Change

v1 used API keys in query parameters.
v2 requires Bearer tokens in headers.

**Migration Steps:**
1. Generate a new access token from the dashboard
2. Replace `?api_key=xxx` with `Authorization: Bearer xxx`
```

---

## Error Documentation

### Standard Error Format

```yaml
components:
  schemas:
    Error:
      type: object
      required:
        - code
        - message
      properties:
        code:
          type: string
          description: Machine-readable error code
          example: "user_not_found"
        message:
          type: string
          description: Human-readable error message
          example: "The requested user does not exist"
        details:
          type: object
          description: Additional error context
          additionalProperties: true
        requestId:
          type: string
          description: Request ID for support
          example: "req_abc123"
```

### Error Code Documentation

```markdown
## Error Codes

| Code | HTTP Status | Description | Resolution |
|:-----|:------------|:------------|:-----------|
| `invalid_request` | 400 | Request body is malformed | Check JSON syntax |
| `authentication_required` | 401 | No auth token provided | Add Bearer token |
| `insufficient_permissions` | 403 | Token lacks required scope | Request additional scopes |
| `resource_not_found` | 404 | Resource doesn't exist | Verify resource ID |
| `rate_limit_exceeded` | 429 | Too many requests | Wait and retry |
| `internal_error` | 500 | Server error | Contact support |
```

---

## Interactive Features

### Try-It-Now Configuration

```javascript
// Swagger UI with authentication
const ui = SwaggerUIBundle({
  url: "/openapi.json",
  dom_id: '#swagger-ui',
  presets: [SwaggerUIBundle.presets.apis],
  plugins: [SwaggerUIBundle.plugins.DownloadUrl],
  
  // OAuth2 configuration
  oauth2RedirectUrl: window.location.origin + '/oauth2-redirect.html',
  
  // Persist authorization
  persistAuthorization: true,
  
  // Custom request interceptor
  requestInterceptor: (request) => {
    // Add custom headers
    request.headers['X-Request-ID'] = crypto.randomUUID();
    return request;
  },
  
  // Response interceptor for logging
  responseInterceptor: (response) => {
    console.log(`${response.url}: ${response.status}`);
    return response;
  }
});
```

---

## AI-Powered Documentation

### Automated Content Generation

```python
# Using OpenAI to generate documentation
from openai import OpenAI

def generate_endpoint_docs(endpoint_spec: dict) -> str:
    client = OpenAI()
    
    prompt = f"""
    Generate comprehensive API documentation for this endpoint:
    
    {json.dumps(endpoint_spec, indent=2)}
    
    Include:
    1. Clear description of what the endpoint does
    2. Use cases and when to use this endpoint
    3. Example request with realistic data
    4. Example response
    5. Common errors and how to handle them
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content
```
