# Backend Modular Architecture Cheat Sheet

## 🎯 Core Concept for Backend
Each module is a **backend domain unit** with two APIs:
- **`module_api/`** - Public interface for other backend modules
- **`http_api/`** - REST endpoints for the module's own frontend only

**Golden Rule:** Modules NEVER import from each other's `internal/` or `http_api/` directories.

## 📁 Backend Directory Structure

```
backend/modules/{module-name}/
├── module_api/                  # Public API for other backend modules
│   ├── __init__.py             # Export service classes & types
│   ├── {module}_service.py     # Thin service orchestration
│   └── types.py                # Shared data types
├── http_api/                   # FastAPI routes for frontend
│   ├── __init__.py
│   ├── routes.py               # FastAPI endpoints
│   └── schemas.py              # Pydantic request/response models
├── domain/                     # Core domain logic (business rules)
│   ├── entities/               # Domain entities (rich objects)
│   │   └── {entity}.py
│   ├── policies/               # Cross-entity authorization/validation
│   │   └── {policy}.py
│   └── exceptions.py           # Domain-specific exceptions
├── infrastructure/             # Technical details (DB, integrations)
│   ├── models/                 # SQLAlchemy/database models
│   │   └── {entity}.py
│   ├── repositories/           # Data access layer
│   │   └── {entity}_repository.py
│   └── mappers.py              # Conversions domain ↔ persistence
└── tests/
    ├── test_{module}_unit.py          # Unit tests (mocked dependencies)
    └── test_{module}_integration.py   # Integration tests (real implementations)
```

## 🔌 Module API Pattern (Backend ↔ Backend)

### 1. Define Service Class
```python
# /modules/users/module_api/user_service.py
from typing import Optional, List
from .types import User, UserCreateRequest

class UserService:
    @staticmethod
    def get_user(user_id: int) -> Optional[User]:
        """Public API: Get user by ID"""
        from ..internal.business_logic import get_user_by_id
        return get_user_by_id(user_id)

    @staticmethod
    def create_user(user_data: UserCreateRequest) -> User:
        """Public API: Create new user"""
        from ..internal.business_logic import create_new_user
        return create_new_user(user_data)

    @staticmethod
    def validate_permissions(user_id: int, resource: str) -> bool:
        """Public API: Check user permissions"""
        from ..internal.business_logic import check_permissions
        return check_permissions(user_id, resource)

    @staticmethod
    def get_users_by_role(role: str) -> List[User]:
        """Public API: Get users with specific role"""
        from ..internal.business_logic import find_users_by_role
        return find_users_by_role(role)
```

### 2. Export in __init__.py
```python
# /modules/users/module_api/__init__.py
from .user_service import UserService
from .types import User, UserCreateRequest, UserPermissions

# Only export what other modules should use
__all__ = ['UserService', 'User', 'UserCreateRequest', 'UserPermissions']
```

### 3. Define Shared Types
```python
# /modules/users/module_api/types.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class User:
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

@dataclass
class UserCreateRequest:
    name: str
    email: str
    role: str = "user"

@dataclass
class UserPermissions:
    user_id: int
    permissions: List[str]
```

## 🌐 HTTP API Pattern (Frontend ↔ Backend)

### FastAPI Routes
```python
# /modules/users/http_api/routes.py
from fastapi import APIRouter, HTTPException, Depends
from ..module_api import UserService
from .schemas import UserResponse, UserCreateRequest, ErrorResponse

# Module-specific prefix
router = APIRouter(
    prefix="/api/v1/users",
    tags=["users-internal"],
    responses={404: {"model": ErrorResponse}}
)

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Internal endpoint: Only for users module frontend"""
    user = UserService.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreateRequest):
    """Internal endpoint: Create user"""
    return UserService.create_user(user_data)

@router.get("/users/{user_id}/permissions/{resource}")
async def check_permissions(user_id: int, resource: str):
    """Internal endpoint: Check user permissions"""
    has_permission = UserService.validate_permissions(user_id, resource)
    return {"has_permission": has_permission}

@router.get("/users", response_model=List[UserResponse])
async def list_users(role: Optional[str] = None):
    """Internal endpoint: List users"""
    if role:
        return UserService.get_users_by_role(role)
    return UserService.get_all_users()
```

### Pydantic Schemas
```python
# /modules/users/http_api/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreateRequest(BaseModel):
    name: str
    email: EmailStr
    role: str = "user"

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class ErrorResponse(BaseModel):
    detail: str
```

## 🏗️ Internal Implementation

### Business Logic
```python
# /modules/users/internal/business_logic.py
from typing import Optional, List
from ..models.user import User as UserModel
from ..module_api.types import User, UserCreateRequest
from .repository import UserRepository

def get_user_by_id(user_id: int) -> Optional[User]:
    """Internal: Get user by ID"""
    user_model = UserRepository.get_by_id(user_id)
    if not user_model:
        return None
    return _model_to_dataclass(user_model)

def create_new_user(user_data: UserCreateRequest) -> User:
    """Internal: Create new user"""
    # Business validation
    if UserRepository.get_by_email(user_data.email):
        raise ValueError("Email already exists")

    # Create user
    user_model = UserRepository.create(user_data)
    return _model_to_dataclass(user_model)

def check_permissions(user_id: int, resource: str) -> bool:
    """Internal: Check if user has permission for resource"""
    user = UserRepository.get_by_id(user_id)
    if not user or not user.is_active:
        return False

    # Permission logic here
    return _has_permission(user, resource)

def find_users_by_role(role: str) -> List[User]:
    """Internal: Find users by role"""
    user_models = UserRepository.get_by_role(role)
    return [_model_to_dataclass(u) for u in user_models]

def _model_to_dataclass(user_model: UserModel) -> User:
    """Convert SQLAlchemy model to dataclass"""
    return User(
        id=user_model.id,
        name=user_model.name,
        email=user_model.email,
        role=user_model.role,
        is_active=user_model.is_active,
        created_at=user_model.created_at
    )

def _has_permission(user: UserModel, resource: str) -> bool:
    """Check user permissions"""
    # Implement permission logic
    admin_resources = ["delete_user", "modify_roles"]
    if resource in admin_resources:
        return user.role == "admin"
    return True
```

### Repository Pattern
```python
# /modules/users/internal/repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.user import User as UserModel
from ...shared.database import get_db

class UserRepository:
    @staticmethod
    def get_by_id(user_id: int) -> Optional[UserModel]:
        with get_db() as db:
            return db.query(UserModel).filter(UserModel.id == user_id).first()

    @staticmethod
    def get_by_email(email: str) -> Optional[UserModel]:
        with get_db() as db:
            return db.query(UserModel).filter(UserModel.email == email).first()

    @staticmethod
    def get_by_role(role: str) -> List[UserModel]:
        with get_db() as db:
            return db.query(UserModel).filter(UserModel.role == role).all()

    @staticmethod
    def create(user_data) -> UserModel:
        with get_db() as db:
            user = UserModel(
                name=user_data.name,
                email=user_data.email,
                role=user_data.role
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    @staticmethod
    def update(user_id: int, updates: dict) -> Optional[UserModel]:
        with get_db() as db:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if user:
                for key, value in updates.items():
                    setattr(user, key, value)
                db.commit()
                db.refresh(user)
            return user

    @staticmethod
    def delete(user_id: int) -> bool:
        with get_db() as db:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if user:
                db.delete(user)
                db.commit()
                return True
            return False
```

## 🔗 Cross-Module Communication

### ✅ Correct Way
```python
# In orders module
from modules.users.module_api import UserService

def process_order(order_data, user_id: int):
    # Use the public module API
    if not UserService.validate_permissions(user_id, "create_order"):
        raise PermissionError("User cannot create orders")

    user = UserService.get_user(user_id)
    if not user:
        raise ValueError("Invalid user")

    # Process order...
```

### ❌ Wrong Ways
```python
# DON'T: Import from internal
from modules.users.internal.business_logic import get_user_by_id

# DON'T: Import from http_api
from modules.users.http_api.routes import get_user

# DON'T: Make HTTP calls to other modules
import requests
response = requests.get("/api/v1/users/users/123")
```

## 🗄️ Database Models

```python
# /modules/users/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from ...shared.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String(50), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

## 🔧 FastAPI App Integration

### Main App
```python
# /backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all module routers
from modules.users.http_api.routes import router as users_router
from modules.orders.http_api.routes import router as orders_router
from modules.notifications.http_api.routes import router as notifications_router

app = FastAPI(title="Modular API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include module routers
app.include_router(users_router)
app.include_router(orders_router)
app.include_router(notifications_router)

@app.get("/")
def root():
    return {"message": "Modular FastAPI Application"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

## 🧪 Testing Patterns

### Unit Tests (test_{module}_unit.py)
```python
# /modules/users/tests/test_users_unit.py
import pytest
from unittest.mock import MagicMock, patch
from modules.users.module_api import UserService
from modules.users.module_api.types import UserCreateRequest

class TestUserService:
    @pytest.fixture
    def mock_repository(self):
        """Mock repository for isolated testing."""
        return MagicMock()

    def test_get_user_success(self, mock_repository):
        with patch('modules.users.infrastructure.UserRepository', mock_repository):
            mock_repository.get_by_id.return_value = User(id=1, name="Test User")

            user = UserService.get_user(1)
            assert user is not None
            assert user.id == 1
            assert user.name == "Test User"

    def test_create_user_validation(self, mock_repository):
        with patch('modules.users.infrastructure.UserRepository', mock_repository):
            user_data = UserCreateRequest(
                name="New User",
                email="new@example.com",
                role="user"
            )
            user = UserService.create_user(user_data)
            mock_repository.create.assert_called_once()

    def test_validate_permissions_logic(self):
        # Test business logic without database
        assert UserService.validate_permissions(admin_user, "delete_user") == True
        assert UserService.validate_permissions(regular_user, "delete_user") == False
```

### Integration Tests (test_{module}_integration.py)
```python
# /modules/users/tests/test_users_integration.py
import pytest
from fastapi.testclient import TestClient
from modules.users.module_api import create_user_service

class TestUserIntegration:
    @pytest.fixture
    def user_service(self):
        """Real service with in-memory or test database."""
        return create_user_service(use_test_db=True)

    @pytest.fixture
    def test_client(self, user_service):
        """Test client with real service integration."""
        from main import app
        app.dependency_overrides[get_user_service] = lambda: user_service
        return TestClient(app)

    async def test_user_creation_flow(self, user_service):
        """Test complete user creation flow."""
        user_data = UserCreateRequest(
            name="Integration Test User",
            email="integration@example.com"
        )

        # Test service layer
        user = await user_service.create_user(user_data)
        assert user.name == "Integration Test User"

        # Verify persistence
        retrieved_user = await user_service.get_user(user.id)
        assert retrieved_user.email == "integration@example.com"

    def test_http_api_integration(self, test_client):
        """Test HTTP API with real service."""
        response = test_client.post("/api/v1/users/users", json={
            "name": "HTTP Test User",
            "email": "http@example.com"
        })

        assert response.status_code == 201
        user_data = response.json()

        # Test retrieval
        get_response = test_client.get(f"/api/v1/users/users/{user_data['id']}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "HTTP Test User"
```

## 📋 Quick Implementation Checklist

### Creating a New Backend Module:

1. **Setup Structure:**
   - [ ] Create module directory: `backend/modules/{module-name}/`
   - [ ] Create subdirectories: `module_api/`, `http_api/`, `domain/`, `infrastructure/`, `tests/`

2. **Implement Domain Layer:**
   - [ ] Create entities in `domain/entities/{entity}.py`
   - [ ] Create policies in `domain/policies/{policy}.py`
   - [ ] Define domain exceptions in `domain/exceptions.py`
   - [ ] Create domain services if needed

3. **Implement Infrastructure:**
   - [ ] Create database models in `infrastructure/models/`
   - [ ] Create repositories in `infrastructure/repositories/`
   - [ ] Create mappers for domain ↔ model conversion

4. **Implement Service Layer:**
   - [ ] Create thin service class in `module_api/{module}_service.py`
   - [ ] Define types in `module_api/types.py`
   - [ ] Export in `module_api/__init__.py`

5. **Implement HTTP API:**
   - [ ] Create FastAPI routes in `http_api/routes.py`
   - [ ] Define Pydantic schemas in `http_api/schemas.py`
   - [ ] Create exception handlers in `http_api/exception_handlers.py`
   - [ ] Add router to main FastAPI app

6. **Add Tests:**
   - [ ] Create unit tests in `tests/test_{module}_unit.py`
   - [ ] Create integration tests in `tests/test_{module}_integration.py` (only if minimal mocking needed)
   - [ ] Ensure tests can be run via `scripts/run_unit.py` and `scripts/run_integration.py`
## 🚫 Common Mistakes to Avoid

```python
# ❌ DON'T: Fat service with business logic
class UserService:
    @staticmethod
    def promote_user(user_id: int, new_role: str) -> User:
        # 100+ lines of business logic in service - WRONG!
        if user.role == "intern" and new_role == "senior":
            raise InvalidPromotionError("Cannot skip junior")
        # ... lots more business rules

# ✅ DO: Thin service orchestrating domain
class UserService:
    @staticmethod
    def promote_user(user_id: int, new_role: str, promoted_by: int) -> User:
        user = UserRepository.get_by_id(user_id)
        promoter = UserRepository.get_by_id(promoted_by)

        PromotionPolicy.authorize_promotion(promoter, user, new_role)
        promotion = user.promote_to(new_role)  # Domain handles logic

        UserRepository.save(user)
        EventBus.publish(UserPromotedEvent(promotion))
        return user

# ❌ DON'T: Domain logic in routes
@router.post("/users/{user_id}/promote")
async def promote_user(user_id: int, new_role: str):
    # Business logic in route - WRONG!
    user = UserRepository.get_by_id(user_id)
    if user.years_of_service < 2 and new_role == "manager":
        raise HTTPException(400, "Need 2+ years")

# ✅ DO: Routes only handle HTTP concerns
@router.post("/users/{user_id}/promote")
async def promote_user(user_id: int, promotion_data: PromotionRequest):
    try:
        user = UserService.promote_user(user_id, promotion_data.new_role)
        return user
    except InvalidPromotionError as e:
        raise HTTPException(status_code=422, detail=str(e))

# ❌ DON'T: Import from other modules' internals
from modules.users.domain.entities.user import User  # WRONG!
from modules.users.infrastructure.repositories.user_repository import UserRepository  # WRONG!

# ✅ DO: Use module APIs only
from modules.users.module_api import UserService, User  # CORRECT!

# ❌ DON'T: HTTP calls between backend modules
import httpx
response = httpx.get("http://localhost:8000/api/v1/users/users/123")  # WRONG!

# ✅ DO: Use module service APIs
user = UserService.get_user(123)  # CORRECT!
```

## 🎯 Layer Interaction Rules

### ✅ Allowed Dependencies:
```
Route Layer     → Service Layer
Service Layer   → Domain Layer + Infrastructure Layer
Domain Layer    → Domain Layer (other entities/policies)
Infrastructure  → Domain Layer (for interfaces)
```

### ❌ Forbidden Dependencies:
```
Domain Layer    → Service Layer    ❌
Domain Layer    → Route Layer      ❌
Domain Layer    → Infrastructure   ❌ (except interfaces)
Infrastructure  → Service Layer    ❌
Infrastructure  → Route Layer      ❌
```

## 🧪 Testing Strategy

### Unit Tests (Fast, Isolated)
- **Purpose**: Test business logic and service orchestration in isolation
- **File**: `test_{module}_unit.py`
- **Dependencies**: All external dependencies mocked
- **Run with**: `python scripts/run_unit.py [--module {module}]`

```python
# Focus on domain logic and service orchestration
def test_user_promotion_business_rules():
    user = User(id=1, name="John", role="junior", years_of_service=2.5)
    promotion = user.promote_to("senior")  # Domain logic
    assert user.role == "senior"

@patch('modules.users.infrastructure.UserRepository')
def test_service_orchestration(mock_repo):
    mock_repo.get_by_id.return_value = User(id=1, role="junior")
    result = UserService.promote_user(1, "senior", 2)  # Service orchestration
    mock_repo.save.assert_called_once()
```

### Integration Tests (Real Flow)
- **Purpose**: Test complete flows with real implementations
- **File**: `test_{module}_integration.py`
- **Dependencies**: Real implementations (in-memory DB, test APIs, real services)
- **When to write**: Only when you can use real implementations with minimal/no mocking
- **When to skip**: If extensive mocking is required (write unit tests instead)
- **Run with**: `python scripts/run_integration.py [--module {module}]`

```python
# Test complete flows end-to-end
async def test_user_creation_complete_flow(user_service):
    # Real service with test database
    user = await user_service.create_user(user_data)
    retrieved = await user_service.get_user(user.id)
    assert retrieved.email == user_data.email

def test_http_api_complete_flow(test_client):
    # Real HTTP client with real service
    response = test_client.post("/api/v1/users", json=user_data)
    assert response.status_code == 201

    user_id = response.json()["id"]
    get_response = test_client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 200
```

### When to Write Integration Tests

**✅ Good candidates for integration tests:**
- Modules with self-contained logic (e.g., `learning_session` with in-memory repository)
- Modules that can use real implementations without external dependencies
- HTTP API testing with real service but test database
- LLM services that can make real API calls (marked appropriately for cost)

**❌ Skip integration tests when:**
- Extensive mocking of external services is required
- Module depends heavily on other modules that would need mocking
- The "integration" test is essentially a unit test with more setup

**Example: Learning Session module** ✅
```python
# Good integration test - uses real in-memory repository
def test_complete_session_flow(learning_session_service):
    session = await learning_session_service.create_session(request)
    await learning_session_service.add_interaction(session.id, interaction)
    completed = await learning_session_service.complete_session(session.id)
    assert completed.status == "completed"
```

**Example: Topic Catalog module** ❌
```python
# Bad integration test - requires extensive mocking of content_creation_service
@patch('content_creation_service.get_all_topics')  # This is a unit test!
def test_browse_topics(mock_service):
    # If you need extensive mocking, write unit tests instead
```

## 🎯 Quick Decision Framework

**Where should this code go?**

1. **"Is this HTTP request/response handling?"**
   - YES → Route Layer

2. **"Is this coordinating multiple entities or external systems?"**
   - YES → Service Layer

3. **"Is this a business rule about one entity?"**
   - YES → Domain Entity

4. **"Is this authorization across multiple entities?"**
   - YES → Policy

5. **"Is this data access or external integration?"**
   - YES → Infrastructure Layer

## 🚀 Benefits Summary

- **Domain Layer**: Testable business logic without infrastructure
- **Service Layer**: Clear orchestration without business complexity
- **Route Layer**: Simple HTTP translation without business knowledge
- **Policy Layer**: Complex authorization rules in one place
- **Infrastructure**: Data access isolated from business logic

The key is keeping each layer focused on its single responsibility!