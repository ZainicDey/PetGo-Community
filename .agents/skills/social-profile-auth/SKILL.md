---
name: social-profile-auth
description: Guidelines and best practices for enforcing social profile completion before allowing write actions (posting, commenting, liking, following) in the social networking app.
---

# Social Profile Authentication Rules

When working on user interactions, endpoints, or creating new features that require user participation, follow these structural rules:

## 1. Read Operations vs Write Operations
* **Read-Only / Consumption**: Use `get_current_user` (or no auth depending on privacy). Users who have registered but have not set up a profile are allowed to read the feed, view posts, and read comments.
* **Write / Participation**: Always use the `require_social_profile` dependency. Users MUST have a fully setup social profile to post, comment, like, follow, or repost.

## 2. Using `require_social_profile`
Do **not** use `get_current_user` for endpoints that involve modifying or creating social graph data. Instead, import and use the custom dependency from `app.dependencies`:

```python
from app.dependencies import require_social_profile

@router.post("/", response_model=MyResponseModel)
async def create_some_social_action(
    data: ActionCreate,
    current_user: DjangoUser = Depends(require_social_profile), # <-- Use this!
    db: Session = Depends(get_social_db)
):
    ...
```
This guarantees `current_user.social_profile` exists and returns a `403 Forbidden` if it does not.

## 3. Frontend UX helper
If you are adding functionality that requires the frontend to know the user's status, remember that the `/users/me` endpoint returns a `has_social_profile` boolean. Do not duplicate this logic on the frontend; instead, rely on the `has_social_profile` field to conditionally render forms or trigger setup redirects.

### Frontend Implementation Example (React/Next.js)
When the app loads, fetch the user state and store it globally:
```javascript
// Fetch user on load
const response = await fetch('/users/me', { headers: { Authorization: `Bearer ${token}` } });
const user = await response.json();
setUser(user); // user.has_social_profile is either true or false
```

When rendering UI elements that require a profile:
```javascript
function PostButton({ user }) {
  const handleClick = () => {
    if (!user.has_social_profile) {
      // Prompt user to complete profile
      showModal("Please complete your profile to post!");
      // OR redirect: router.push('/complete-profile');
      return;
    }
    // Proceed with posting...
  };

  return <button onClick={handleClick}>Create Post</button>;
}
```
