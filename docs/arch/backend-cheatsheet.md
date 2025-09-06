# 🧩 Backend Modular Architecture Cheat Sheet (FastAPI / Python)

## 🎯 Core Concept

Each module is a **backend domain unit** with strict layering and two interfaces:

* **`module_api/`** — Public interface for **other backend modules** (no HTTP)
* **`http_api/`** — REST endpoints for this module’s **own frontend** only

**Golden Rule:** Cross-module imports must go through **`module_api/`**.
Never import another module’s `domain/`, `infrastructure/`, or `http_api/`.

---

## 📁 Layers → Directories

| **Layer**                | **Directory**     | **Purpose**                                                      |
| ------------------------ | ----------------- | ---------------------------------------------------------------- |
| **Service Layer**        | `module_api/`     | Thin services (orchestration) + exported types for other modules |
| **Route Layer**          | `http_api/`       | FastAPI routers + Pydantic schemas (HTTP translation only)       |
| **Domain Layer**         | `domain/`         | Pure business logic: entities, policies, exceptions              |
| **Infrastructure Layer** | `infrastructure/` | DB models, repositories, persistence mappers, external adapters  |
| **Tests**                | `tests/`          | Unit & integration tests per layer                               |

---

## 📂 Directory Structure (template)

```
backend/modules/{module-name}/
├── module_api/
│   ├── __init__.py
│   ├── {module}_service.py      # thin orchestration; no business rules here
│   └── types.py                 # exported dataclasses / DTOs
├── http_api/
│   ├── __init__.py
│   ├── routes.py                # FastAPI endpoints
│   └── schemas.py               # Pydantic models (request/response)
├── domain/
│   ├── entities/                # rich domain objects
│   ├── policies/                # cross-entity authorization/validation
│   └── exceptions.py
├── infrastructure/
│   ├── models/                  # SQLAlchemy models
│   ├── repositories/            # data access
│   └── mappers.py               # domain ↔ persistence conversions
└── tests/
    ├── test_{module}_unit.py          # Unit tests (mocked)
    └── test_{module}_integration.py   # Integration tests (real)
```

---

## 🏗️ Responsibilities (at a glance)

* **module\_api/**: Public, thin services that coordinate domain + infra; expose only what other modules need.
* **http\_api/**: HTTP-only concerns (routing, validation, serialization). No domain rules.
* **domain/**: Business rules in entities/policies; pure, testable; no DB/HTTP.
* **infrastructure/**: Technical details (ORM, repos, external services).
* **tests/**: Rich domain tests, isolated service tests, route tests via TestClient.

---

## 🔄 Data Flow

```
Frontend ↔ http_api/routes.py → module_api/{module}_service.py → domain/* + infrastructure/*
```

---

## 🤝 Interface Contracts

**Route ↔ Service**

```python
# http_api/routes.py
@router.post("/users")
def create_user(req: UserCreateRequest):
    return UserService.create_user(req)
```

**Service ↔ Domain + Infra**

```python
# module_api/user_service.py
def create_user(req: UserCreateRequest) -> User:
    if not EmailPolicy.is_valid(req.email):  # domain policy
        raise InvalidEmailError()
    model = UserRepository.create(req)       # infrastructure
    return map_model_to_user(model)          # mapper to exported type
```

---

## ✅ Best Practices

* Keep **services thin**; push business rules into **domain**.
* Keep **routes dumb**; only translate HTTP ↔ service calls.
* Repositories return **models**; convert to exported **types** at boundaries.
* One module’s **frontend** calls its **http\_api**; other backend modules call its **module\_api** (never HTTP).

---

## 🚫 Anti-Patterns

* Putting business logic in **routes** or **services**.
* Importing another module’s **domain/infrastructure/http\_api**.
* Making HTTP calls between backend modules.
* Returning ORM models directly from **module\_api**.

---

## 🔐 Import Rules (copy/paste into PRs)

* ✅ Cross-module import path: `from modules.{other}.module_api import ...`
* ❌ Forbidden: `modules.{other}.domain.*`, `modules.{other}.infrastructure.*`, `modules.{other}.http_api.*`

---

## 🧪 Testing Strategy

* **Unit Tests (`test_{module}_unit.py`)**: Mock all dependencies; test business logic & orchestration in isolation.
* **Integration Tests (`test_{module}_integration.py`)**: Real implementations; test complete flows end-to-end. **Only write if minimal/no mocking needed.**
* **Run Tests**: `python scripts/run_unit.py [--module {module}]` or `python scripts/run_integration.py [--module {module}]`

---

## 📝 Quick Implementation Checklist

1. **Scaffold module:** `module_api/`, `http_api/`, `domain/`, `infrastructure/`, `tests/`.
2. **Domain:** entities, policies, exceptions.
3. **Infra:** SQLAlchemy models, repositories, mappers.
4. **Service:** thin methods in `{module}_service.py` using domain + repos; export types.
5. **HTTP:** routes + Pydantic schemas; wire router into app.
6. **Tests:** Create `test_{module}_unit.py` (mocked). Only create `test_{module}_integration.py` if minimal mocking needed.

---

## 🧭 Quick Decision Guide

* **HTTP parsing/validation?** → `http_api/`
* **Coordinating repos & domain?** → `module_api/`
* **Business rule (single entity/aggregate)?** → `domain/`
* **DB/external system access?** → `infrastructure/`
