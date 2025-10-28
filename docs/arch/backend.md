
# Simple Modular Scheme (Service returns DTOs; Public returns Service)

```
modules/{name}/
├── models.py            # SQLAlchemy ORM tables (schema only, use "Model" suffix on model names)
├── repo.py              # DB access (returns ORM)
├── service.py           # Use-cases; returns DTOs (Pydantic or dataclass)
├── public.py            # 🚪 Narrow contract + DI provider (returns the service directly)
├── routes.py            # FastAPI endpoints (HTTP-only concerns)
└── test_{name}_unit.py  # Unit tests (Keep them minimal in number and cover complex behavior, not simple getters, etc.)
└── <others>             # Add other files and directories as needed to implement complex service methods.
```
*Note: integration tests spanning modules are in a global tests directory

## Rules

* **Service returns DTOs** (never ORM).
* **Public** exposes a **Protocol** and returns the **service instance directly**.
* **Routes** use the service; **other modules import only from `module.public`**.
* **Routes** URLs match the module name, e.g. `/api/v1/users` for the `users` module.
* Transactions live in a request-scoped `get_session()` (commit/rollback there).
* The only way another module can access this module is through the public.py interface!
* Don't create routes or public APIs unless there is a demonstrated need for them.
* If you add new routes, add the router to the server.py file.

---

## Complete minimal example — `modules/users/` (sync SQLAlchemy)

### models.py

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from modules.shared_models import Base


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### repo.py

```python
from sqlalchemy.orm import Session
from .models import UserModel


class UserRepo:
    def __init__(self, session: Session):
        self.s = session

    def by_id(self, user_id: int) -> UserModel | None:
        return self.s.get(UserModel, user_id)

    def by_email(self, email: str) -> UserModel | None:
        return self.s.query(UserModel).filter(UserModel.email == email).first()

    def add(self, user: UserModel) -> UserModel:
        self.s.add(user)
        self.s.flush()
        return user

    def save(self, user: UserModel) -> None:
        self.s.add(user)
```

### service.py  *(DTOs live here; service returns DTOs)*

```python
from pydantic import BaseModel, EmailStr
from .repo import UserRepo
from .models import UserModel


class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    name: str


class UserService:
    def __init__(self, repo: UserRepo) -> None:
        self.repo = repo

    def get(self, user_id: int) -> UserRead | None:
        u = self.repo.by_id(user_id)
        return UserRead.model_validate(u) if u else None

    def register(self, data: UserCreate) -> UserRead:
        if self.repo.by_email(data.email):
            raise ValueError("Email already exists")
        created = self.repo.add(UserModel(email=data.email, name=data.name, role="user"))
        return UserRead.model_validate(created)

    def has_permission(self, user_id: int, resource: str) -> bool:
        u = self.repo.by_id(user_id)
        if not u or not u.is_active:
            return False
        return resource != "delete_user" or u.role == "admin"
```

### public.py  *(no remapping—returns the service directly)*

```python
from typing import Protocol, Optional
from sqlalchemy.orm import Session
from .repo import UserRepo
from .service import UserService, UserRead


class UsersProvider(Protocol):
    def get(self, user_id: int) -> Optional[UserRead]: ...
    def has_permission(self, user_id: int, resource: str) -> bool: ...


def users_provider(session: Session) -> "UsersProvider":
    # Return the concrete service; it already returns DTOs
    return UserService(UserRepo(session))


__all__ = ["UsersProvider", "users_provider", "UserRead"]
```

### routes.py

```python
from collections.abc import Generator
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from modules.infrastructure.public import infrastructure_provider
from .repo import UserRepo
from .service import UserService, UserRead, UserCreate

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def get_session() -> Generator[Session, None, None]:
    """Request-scoped database session with auto-commit."""
    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as s:
        yield s


def get_user_service(s: Session = Depends(get_session)) -> UserService:
    """Build UserService for this request - use service directly, not public interface."""
    return UserService(UserRepo(s))


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, svc: UserService = Depends(get_user_service)) -> UserRead:
    u = svc.get(user_id)
    if not u:
        raise HTTPException(404, "User not found")
    return u


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, svc: UserService = Depends(get_user_service)) -> UserRead:
    try:
        return svc.register(body)
    except ValueError as e:
        raise HTTPException(409, detail=str(e))
```

---

## Using it from another module

Cross-module dependencies should typically be injected at the **service layer**, not in routes:

```python
# modules/orders/service.py
from modules.users.public import UsersProvider

class OrderService:
    def __init__(self, users: UsersProvider):
        self.users = users  # Use other module's public interface

    def create(self, user_id: int, sku: str):
        if not self.users.has_permission(user_id, "create_order"):
            raise PermissionError("forbidden")
        if not self.users.get(user_id):
            raise LookupError("user not found")
        # proceed...

# modules/orders/routes.py
from modules.users.public import users_provider
from .service import OrderService

def get_order_service(s: Session = Depends(get_session)) -> OrderService:
    users_service = users_provider(s)  # Same session = same transaction
    return OrderService(users_service)
```

### Key Principles:
- **Within a module**: Routes use the service directly (`UserService`)
- **Cross-module**: Services use other modules' public interfaces (`UsersProvider`)
- **Public interfaces**: Only for consumption by *other* modules

---

## Notes

* Boundary safety: **Service & public return DTOs**, so no ORM leaks.
* No facade: **public returns the service directly**; enforcement is by convention (import only from `module.public`) and, if you wish, a linter rule.
* Keep sessions request-scoped in `get_session()` (commit/rollback there).
* Pick sync **or** async across repo/service/routes and stick to it (use async if depending on any modules that have async public interfaces).
* Oversized service modules can promote helpers into a `service/` package while keeping `service.py` as a thin façade. Extract DTOs into `service/dtos.py`, move focused logic into handler modules, and have the façade delegate:

```python
# modules/content/service.py
from .service.lesson_handler import LessonHandler
from .service.unit_handler import UnitHandler

class ContentService:
    def __init__(self, repo: ContentRepo, object_store: ObjectStoreProvider | None = None) -> None:
        media = MediaHelper(object_store)
        self._lessons = LessonHandler(repo, media)
        self._units = UnitHandler(repo, media, self._lessons)

    async def get_lesson(self, lesson_id: str) -> LessonRead | None:
        return await self._lessons.get_lesson(lesson_id)
```

The façade owns lifecycle/dependency wiring, but each handler remains private to the module.
