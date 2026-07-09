# Role-Based Access Control (RBAC) & Document Scoping

DocSight secures document access at the database and query boundary level using a tag-based Role-Based Access Control (RBAC) model. Document scoping is enforced dynamically during search query evaluation.

## 1. User Roles & Permission Levels

| Role | Role Value | Document Scope | Administrative Rights |
| :--- | :--- | :--- | :--- |
| **Operator** | `operator` | Restricted strictly to documents matching tags in `UserProfile.allowed_tags` | None |
| **Supervisor** | `supervisor` | Restricted strictly to documents matching tags in `UserProfile.allowed_tags` | None |
| **Administrator** | `admin` | Unrestricted (sees all documents, tags, and audit trails) | Django Admin panel, creating users |

---

## 2. Database Model Schema

The security boundaries are modeled via a One-to-One profile relation linked to a custom `User` model, extending permissions to individual document tags:

```
+------------------+          1 : 1          +---------------------+
|   Custom User    | ----------------------> |     UserProfile     |
|   (role field)   |                         |  (allowed_tags M2M) |
+------------------+                         +---------------------+
                                                        |
                                                        | N : M
                                                        v
                                             +---------------------+
                                             |         Tag         |
                                             |     (name field)    |
                                             +---------------------+
```

### Models Representation (`apps/authentication/models.py`)

```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        OPERATOR = "operator", "Operator"
        SUPERVISOR = "supervisor", "Supervisor"
        ADMIN = "admin", "Administrator"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OPERATOR)

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    allowed_tags = models.ManyToManyField(Tag, blank=True)
```

---

## 3. Query Scoping Logic

The backend `DocumentSearchService` enforces tag validation before delegating full-text search parameters to the search client.

```
Incoming Request (User: operator_a, Tags Requested: ["tag-1", "tag-2"])
                  |
                  v
       Fetch user.profile.allowed_tags ---> ["tag-1", "tag-3"]
                  |
                  v
       Compute Intersection: (Requested Tags) AND (Allowed Tags)
                            ["tag-1", "tag-2"] AND ["tag-1", "tag-3"]
                  |
                  v
       Effective Scoped Search Tags ---> ["tag-1"]
                  |
                  v
       Execute Search (Loom API Client)
```

### Pure Domain Enforcement Code

```python
class DocumentSearchService:
    def __init__(self, engine: AbstractSearchEngine):
        self.engine = engine

    async def search(self, user: User, request: SearchRequest) -> SearchResponse:
        # 1. Fetch user tag scope
        allowed_tags = self._get_allowed_tags(user)
        
        # 2. Intersect request search filters with user scope
        effective_tags = self._intersect_tags(request.tags, allowed_tags)

        # 3. Request search from the engine with effective tags
        return await self.engine.search(
            query=request.query,
            tags=effective_tags,
            file_types=request.file_types,
            page=request.page,
            page_size=request.page_size,
        )

    def _get_allowed_tags(self, user: User) -> list[str] | None:
        """
        Retrieves user tag list from UserProfile.
        Returns None if user is admin (unrestricted access).
        """
        if user.is_superuser or user.role == User.Role.ADMIN:
            return None
        try:
            return list(user.profile.allowed_tags.values_list("name", flat=True))
        except AttributeError:
            return []

    def _intersect_tags(self, requested: list[str] | None, allowed: list[str] | None) -> list[str] | None:
        """
        Calculates search tag intersections.
        - If allowed is None, user is admin -> return requested filters.
        - If requested is empty -> restrict queries to the entire allowed scope.
        - Otherwise -> intersect requested and allowed tags to resolve the scope.
        """
        if allowed is None:
            return requested
        if not requested:
            return allowed
        return list(set(requested) & set(allowed))

## 4. DRF Custom Permission Classes

To protect API endpoints, DocSight defines custom Django REST Framework (DRF) permission classes based on the user's role mapping:

| Permission Class | Allowed Roles | Description / Scope |
| :--- | :--- | :--- |
| `IsAdmin` | `admin` | Restricts access exclusively to users with `role == 'admin'`. |
| `IsSupervisor` | `admin`, `supervisor` | Restricts access to users with `role` as admin or supervisor. |
| `IsOperator` | `admin`, `supervisor`, `operator` | Restricts access to users with any valid role (admin, supervisor, operator). |

### Permission Classes Implementation (`apps/authentication/api/permissions.py`)

```python
from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'admin')

class IsSupervisor(BasePermission):
    def has_permission(self, request, view):
        role = getattr(request.user, 'role', None)
        return bool(request.user and request.user.is_authenticated and role in ['admin', 'supervisor'])

class IsOperator(BasePermission):
    def has_permission(self, request, view):
        role = getattr(request.user, 'role', None)
        return bool(request.user and request.user.is_authenticated and role in ['admin', 'supervisor', 'operator'])
```
