# LLM Module Migration Plan

## Overview

This document outlines the plan to create a new `llm_services` module following the simplified modular architecture defined in `backend.md`. The module will consolidate LLM functionality from the `llm-flow-engine` project into the main backend following the prescribed pattern:

```
modules/llm_services/
├── models.py            # SQLAlchemy ORM tables (LLMRequest)
├── repo.py              # DB access (returns ORM)
├── service.py           # Use-cases; returns DTOs (Pydantic)
├── public.py            # Narrow contract + DI provider
└── test_llm_services_unit.py  # Unit tests
```

## Source Analysis

### Current LLM Flow Engine Structure
The LLM functionality is currently located in `/llm-flow-engine/src/llm_flow_engine/core/llm/` with:

- **Base Classes**: `base.py` - Abstract `LLMProvider` class with database logging
- **Types**: `types.py` - Core data structures (`LLMMessage`, `LLMResponse`, etc.)
- **Configuration**: `config.py` - `LLMConfig` class and environment setup
- **Providers**: `providers/openai_provider.py` - Concrete OpenAI implementation
- **Database Model**: `database/models.py` - `LLMRequest` SQLAlchemy model
- **Additional**: `cache.py`, `exceptions.py` - Supporting functionality

### Key Components to Migrate

1. **LLMRequest Model** - Database tracking of LLM requests/responses
2. **LLM Provider Interface** - Abstract base class for providers
3. **Configuration System** - Environment-based config management
4. **Type Definitions** - Core data structures and enums
5. **Provider Implementations** - OpenAI provider (extensible for others)

## Migration Plan

### Phase 1: Core Module Structure

#### 1.1 Create `models.py`
```python
# backend/modules/llm_services/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Text, Float, JSON
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()

class LLMRequest(Base):
    """SQLAlchemy model for LLM requests - migrated from llm-flow-engine"""
    __tablename__ = "llm_requests"

    # Core fields from existing LLMRequest model
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), nullable=True, index=True)
    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    # ... (all other fields from current LLMRequest)
```

#### 1.2 Create `repo.py`
```python
# backend/modules/llm_services/repo.py
from sqlalchemy.orm import Session
from .models import LLMRequest
import uuid

class LLMRequestRepo:
    def __init__(self, session: Session):
        self.s = session

    def by_id(self, request_id: uuid.UUID) -> LLMRequest | None:
        return self.s.get(LLMRequest, request_id)

    def create(self, llm_request: LLMRequest) -> LLMRequest:
        self.s.add(llm_request)
        self.s.flush()
        return llm_request

    def update_success(self, request_id: uuid.UUID, response_data: dict) -> None:
        # Update request with successful response
        pass

    def update_error(self, request_id: uuid.UUID, error_info: dict) -> None:
        # Update request with error information
        pass
```

#### 1.3 Create `service.py` (DTOs and Business Logic)
```python
# backend/modules/llm_services/service.py
from pydantic import BaseModel
from typing import Optional, List, Any
import uuid
from .repo import LLMRequestRepo

# DTOs
class LLMMessageDTO(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class LLMRequestDTO(BaseModel):
    id: uuid.UUID
    provider: str
    model: str
    status: str
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    # ... other fields
    class Config:
        from_attributes = True

class LLMResponseDTO(BaseModel):
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    # ... other fields

class LLMService:
    def __init__(self, repo: LLMRequestRepo):
        self.repo = repo

    async def generate_response(
        self,
        messages: List[LLMMessageDTO],
        user_id: Optional[uuid.UUID] = None,
        **kwargs
    ) -> tuple[LLMResponseDTO, uuid.UUID]:
        """Generate LLM response and track in database"""
        # Business logic for LLM generation
        pass

    def get_request(self, request_id: uuid.UUID) -> Optional[LLMRequestDTO]:
        """Get LLM request by ID"""
        request = self.repo.by_id(request_id)
        return LLMRequestDTO.model_validate(request) if request else None
```

#### 1.4 Create `public.py` (Module Interface)
```python
# backend/modules/llm_services/public.py
from typing import Protocol, Optional, List, Any, TypeVar
from fastapi import Depends
import uuid
from pydantic import BaseModel
from modules.shared.db import get_session
from .repo import LLMRequestRepo
from .service import LLMService, LLMMessageDTO, LLMResponseDTO, LLMRequestDTO

# Type variable for structured responses
T = TypeVar("T", bound=BaseModel)

class LLMServicesProvider(Protocol):
    """
    Protocol defining the public interface for LLM services.

    This interface provides access to LLM functionality including:
    - Text generation with conversation context
    - Structured output generation using Pydantic models
    - Image generation from text prompts
    - Web search capabilities
    - Request tracking and retrieval
    """

    async def generate_response(
        self,
        messages: List[LLMMessageDTO],
        user_id: Optional[uuid.UUID] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> tuple[LLMResponseDTO, uuid.UUID]:
        """
        Generate a text response from the LLM.

        Args:
            messages: List of conversation messages
            user_id: Optional user identifier for tracking
            model: Override default model (e.g., "gpt-4", "gpt-3.5-turbo")
            temperature: Override default temperature (0.0-2.0)
            max_tokens: Override default max tokens
            **kwargs: Additional provider-specific parameters

        Returns:
            Tuple of (response DTO, request ID for tracking)

        Raises:
            LLMError: If the request fails
        """
        ...

    async def generate_structured_response(
        self,
        messages: List[LLMMessageDTO],
        response_model: type[T],
        user_id: Optional[uuid.UUID] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> tuple[T, uuid.UUID]:
        """
        Generate a structured response using a Pydantic model.

        Args:
            messages: List of conversation messages
            response_model: Pydantic model class for structured output
            user_id: Optional user identifier for tracking
            model: Override default model
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional provider-specific parameters

        Returns:
            Tuple of (structured response object, request ID)

        Raises:
            LLMError: If the request fails
            LLMValidationError: If response doesn't match the model
        """
        ...

    async def generate_image(
        self,
        prompt: str,
        user_id: Optional[uuid.UUID] = None,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        **kwargs: Any
    ) -> tuple[str, uuid.UUID]:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the desired image
            user_id: Optional user identifier for tracking
            size: Image size (e.g., "1024x1024", "512x512")
            quality: Image quality ("standard" or "hd")
            style: Optional style parameter
            **kwargs: Additional provider-specific parameters

        Returns:
            Tuple of (image URL, request ID)

        Raises:
            LLMError: If the request fails
        """
        ...

    async def search_web(
        self,
        queries: List[str],
        user_id: Optional[uuid.UUID] = None,
        max_results: int = 10,
        **kwargs: Any
    ) -> tuple[List[dict], uuid.UUID]:
        """
        Search the web for recent information.

        Args:
            queries: List of search queries
            user_id: Optional user identifier for tracking
            max_results: Maximum number of results per query
            **kwargs: Additional search parameters

        Returns:
            Tuple of (search results list, request ID)

        Raises:
            LLMError: If the search fails
        """
        ...

    def get_request(self, request_id: uuid.UUID) -> Optional[LLMRequestDTO]:
        """
        Retrieve details of a previous LLM request.

        Args:
            request_id: UUID of the request to retrieve

        Returns:
            Request DTO if found, None otherwise
        """
        ...

    def get_user_requests(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[LLMRequestDTO]:
        """
        Get recent requests for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of requests to return
            offset: Number of requests to skip

        Returns:
            List of request DTOs
        """
        ...

    def estimate_cost(
        self,
        messages: List[LLMMessageDTO],
        model: Optional[str] = None
    ) -> float:
        """
        Estimate the cost of a request before making it.

        Args:
            messages: List of conversation messages
            model: Model to use for estimation

        Returns:
            Estimated cost in USD
        """
        ...

def llm_services_provider(session = Depends(get_session)) -> LLMServicesProvider:
    """Dependency injection provider for LLM services."""
    return LLMService(LLMRequestRepo(session))

__all__ = [
    "LLMServicesProvider",
    "llm_services_provider",
    "LLMMessageDTO",
    "LLMResponseDTO",
    "LLMRequestDTO"
]
```


### Phase 2: Core LLM Infrastructure

#### 2.1 Provider System
Create internal provider system within the module:

```
modules/llm_services/
├── providers/
│   ├── __init__.py
│   ├── base.py          # Abstract provider interface
│   ├── openai.py        # OpenAI implementation
│   └── factory.py       # Provider factory
├── config.py            # Configuration management
└── types.py             # Core type definitions
```

#### 2.2 Configuration Integration
- Migrate `LLMConfig` class
- Environment variable handling
- Provider selection logic

#### 2.3 Error Handling
- Migrate exception classes
- Proper error propagation to service layer

### Phase 3: Advanced Features

#### 3.1 Caching System
- Integrate cache functionality from `cache.py`
- Cache configuration in service layer

#### 3.2 Structured Output Support
- Support for Pydantic model responses
- Instructor integration

#### 3.3 Multi-Provider Support
- Abstract provider interface
- Easy addition of new providers (Anthropic, Azure OpenAI)

### Phase 4: Testing Strategy

#### 4.1 Unit Tests
Following the memory guidance for test naming:
```
backend/modules/llm_services/test_llm_services_unit.py
```

Test coverage:
- Service layer business logic
- Provider implementations (mocked)
- Configuration validation
- Error handling

#### 4.2 Integration Tests
```
backend/tests/test_llm_services_integration.py
```

Test coverage:
- End-to-end LLM requests
- Database persistence
- Provider integration (with real API calls in CI)

### Phase 5: Migration Steps

#### 5.1 File Migration Order
1. Create base module structure (`models.py`, `repo.py`, `service.py`, `public.py`)
2. Migrate core types and configuration
3. Migrate provider system
4. Implement service layer logic
5. Add comprehensive tests
6. Update existing code to use new module

#### 5.2 Database Migration
- Create Alembic migration for `llm_requests` table
- Ensure compatibility with existing data if any

#### 5.3 Integration Points
Update existing modules to use the new LLM services:
- `content_creation` module
- Any other modules currently using LLM functionality

## Benefits of This Approach

### 1. Architectural Consistency
- Follows the established modular pattern
- Clear separation of concerns
- Consistent with other modules

### 2. Maintainability
- Single responsibility principle
- Easy to test and mock
- Clear interfaces between layers

### 3. Extensibility
- Easy to add new LLM providers
- Configurable through environment variables
- Supports future enhancements (streaming, function calling, etc.)

### 4. Integration
- Clean dependency injection
- Protocol-based interfaces
- Easy to use from other modules
- No HTTP routes needed - pure service module

## Implementation Timeline

- **Week 1**: Phase 1 - Core module structure
- **Week 2**: Phase 2 - LLM infrastructure migration
- **Week 3**: Phase 3 - Advanced features
- **Week 4**: Phase 4 & 5 - Testing and migration

## Risk Mitigation

1. **Backward Compatibility**: Maintain existing interfaces during transition
2. **Testing**: Comprehensive unit and integration tests
3. **Gradual Migration**: Migrate one component at a time
4. **Rollback Plan**: Keep original code until migration is complete and tested

## Success Criteria

- [ ] All LLM functionality migrated to new module
- [ ] Existing functionality works without changes
- [ ] Comprehensive test coverage (>80%)
- [ ] Documentation updated
- [ ] Performance maintained or improved
- [ ] Clean, maintainable code following established patterns
