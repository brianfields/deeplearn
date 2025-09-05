# 📱 Frontend Modular Architecture Cheat Sheet (React Native)

## 🎯 Core Concept

Each module is a **frontend domain unit** with strict layers.
**Golden Rule:** Cross-module imports must go through **`module_api/`** only.
Never import another module’s `screens/`, `components/`, `domain/`, `http_client/`, `application/`, or `adapters/`.

---

## 📁 Layers → Directories

| **Layer**             | **Directory**  | **Purpose**                                                                                         |
| --------------------- | -------------- | --------------------------------------------------------------------------------------------------- |
| **Screen Layer**      | `screens/`     | Thin UI: render state, handle input, call module API hooks                                          |
| **Module API Layer**  | `module_api/`  | Public surface: thin hooks (React Query), store selectors/actions, navigation helpers, shared types |
| **Application Layer** | `application/` | Use-cases/workflows; orchestrates domain + http\_client + adapters; side effects live here          |
| **Domain Layer**      | `domain/`      | Pure logic: business rules, formatters, utils, private hooks (no I/O)                               |
| **HTTP Client Layer** | `http_client/` | API calls to the module’s backend, mappers, API types                                               |
| **Adapters Layer**    | `adapters/`    | Infrastructure adapters (analytics, notifications, storage)                                         |
| **UI Components**     | `components/`  | Reusable UI within the module (not exported cross-module)                                           |
| **Navigation**        | `navigation/`  | Module stack + param types                                                                          |
| **Tests**             | `tests/`       | Unit + integration tests per layer                                                                  |

---

## 📂 Directory Structure (template)

```
mobile/modules/{module-name}/
├── module_api/
│   ├── index.ts
│   ├── queries.ts
│   ├── store.ts
│   ├── navigation.ts
│   └── types.ts
├── screens/
│   ├── {Entity}ListScreen.tsx
│   ├── {Entity}DetailScreen.tsx
│   ├── {Entity}EditScreen.tsx
│   └── index.ts
├── components/
│   ├── {Entity}Card.tsx
│   ├── {Entity}Form.tsx
│   └── index.ts
├── navigation/
│   ├── {Module}Stack.tsx
│   ├── types.ts
│   └── index.ts
├── http_client/
│   ├── api.ts
│   ├── mappers.ts
│   └── types.ts
├── adapters/
│   ├── analytics.adapter.ts
│   ├── notifications.adapter.ts
│   └── storage.adapter.ts
├── application/
│   ├── {usecase}.usecase.ts
│   └── index.ts
├── domain/
│   ├── business-rules/
│   ├── formatters/
│   ├── hooks/
│   ├── utils/
│   └── styles.ts
└── tests/
    ├── screens/
    ├── components/
    ├── module_api/
    └── integration/
```

---

## 🏗️ Responsibilities (at a glance)

* **screens/**: UI only. ❌ No HTTP, no business rules.
* **module\_api/**: Thin public facade (hooks/selectors/navigation). ❌ No side effects, no HTTP.
* **application/**: Use-cases; coordinate domain + http\_client + adapters; ✅ side effects.
* **domain/**: Pure logic/formatting. ❌ No I/O.
* **http\_client/**: API calls & mapping. ❌ Internal to module.
* **adapters/**: Analytics/notifications/storage. ❌ Internal to module.

---

## 🔄 Data Flow

```
User → screens/ → module_api/ → application/ → http_client/ → Backend
                        ↑              ↑
                   domain/ rules   adapters/
```

---

## 🤝 Interface Contracts

**Screen ↔ Module API**

```ts
const { user, isLoading } = useUserQueries().useUser(userId)
const { navigateToUserEdit } = useUserNavigation()
```

**Module API ↔ Application**

```ts
// module_api/queries.ts (thin)
useMutation({
  mutationFn: ({ id, role }) => promoteUserUseCase(id, role),
})
```

**Application ↔ Infra + Domain**

```ts
// application/promoteUser.usecase.ts
const user = await userApi.getUser(id)
if (!UserBusinessRules.canBePromoted(user)) throw new Error(...)
const updated = await userApi.promoteUser(id, role)
Notifications.success(...)
Analytics.track('user_promoted', { id, role })
return updated
```

---

## ✅ Best Practices

* Keep **screens** tiny; route all data/actions through **module\_api**.
* Put **side effects** (toasts, analytics, storage) in **application/** using **adapters/**.
* Keep **domain/** pure (deterministic, testable).
* Cache & fetch via **React Query** in **module\_api/**; heavy transforms delegated to **domain/**.
* If UI is shared across modules, promote it to **`mobile/shared/ui/*`**.

---

## 🚫 Anti-Patterns

* Fat screens doing HTTP and rules.
* Business rules inside query hooks.
* Cross-module HTTP calls (or importing another module’s internals).
* Putting orchestration/side-effects inside `module_api/`.

---

## 📝 Quick Implementation Checklist

1. **Scaffold module:** `module_api/`, `screens/`, `components/`, `navigation/`, `http_client/`, `application/`, `domain/`, `adapters/`, `tests/`.
2. **Add queries/hooks:** Thin hooks in `module_api/queries.ts` delegating to use-cases.
3. **Create use-cases:** In `application/`, coordinate domain + http\_client + adapters.
4. **Write rules/formatters:** In `domain/`.
5. **Wire API client + mappers:** In `http_client/`.
6. **Build screens/components:** UI only; call `module_api` hooks.
7. **Tests:**

   * Screens mock `module_api`.
   * Module API mocks `application/http_client`.
   * Application tests domain + adapters orchestration.

---

## 🔐 Import Rules (copy/paste into PRs)

* ✅ Import other modules **only** from `@/modules/{name}/module_api`.
* ❌ Never import from `screens/`, `components/`, `domain/`, `http_client/`, `application/`, `adapters/` of another module.
* ❌ No cross-module HTTP.
