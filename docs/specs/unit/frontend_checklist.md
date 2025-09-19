## 0) Structure & Naming

* [x] Module folder is `mobile/modules/{name}/`.
* [x] Required files exist (or are intentionally omitted with a current justification): `models.ts`, `repo.ts`, `service.ts`, `public.ts`, `queries.ts`, `test_{name}_unit.ts`.
* [x] Optional files only when needed: `store.ts`, `nav.tsx`, `screens/`, `components/`.
* [x] Responsibilities match filenames (no HTTP in `service.ts`, no business rules in `queries.ts`, no UI in `service.ts`).

## 1) Imports & Boundaries

* [x] Cross-module imports are **only** from `@/modules/<other>/public`.
* [x] This module **does not import its own `public.ts`**.
* [x] Only `service.ts` imports `repo.ts`.
* [x] `queries.ts` imports **only** this module’s `service.ts` (never `repo.ts`).
* [x] No React/React Query imports in `service.ts` or `repo.ts`.

## 2) Types: Wire vs DTO (models.ts)

* [x] API wire types are named with `Api*` prefix and **not exported** from `public.ts`.
* [x] DTOs are exported types/interfaces used by UI and other modules.
* [x] `service.ts` maps **Api → DTO**; DTOs contain normalized shapes (e.g., `Date` objects, narrowed unions).
* [x] No `Api*` types appear in `public.ts`, `queries.ts`, `screens/`, or `components/`.

## 3) Networking (repo.ts)

* [x] `repo.ts` is the **only** file that performs HTTP (`axios`/`fetch`).
* [x] Base path is limited to **this module’s** routes (vertical slice), e.g., `const MODULE_BASE = '/api/v1/{name}'`.
* [x] All request params/bodies are typed; no `any`.
* [x] Timeouts and headers are set; low-level errors are normalized (no raw Axios errors thrown).
* [x] Supports cancellation (AbortController or axios signal) for long/abortable calls.

## 4) Service Layer (service.ts)

* [x] Exposes use-cases; returns **DTOs only** (`Promise<DTO>` / `Promise<DTO[]>`).
* [x] Performs mapping & business rules (no React/HTTP).
* [x] Cross-module composition imports **only** other modules’ `public` interfaces.
* [x] Throws domain-shaped errors (`NotFoundError`, `PermissionError`, etc.) for callers to translate.

## 5) Public Interface (public.ts)

* [x] Defines a **narrow interface** (what other modules actually consume).
* [x] Provider constructs the concrete `Service` and **forwards** methods (no logic/mapping/conditionals).
* [x] Public surface exports: the interface, the provider, and selected DTO types (no `Api*`, no `Service`, no `Repo`).
* [x] Not imported by files inside the same module (external consumption only).

## 6) Queries & Caching (queries.ts)

* [x] React Query hooks call **service**, never `repo`.
* [x] Query keys are **namespaced** and stable, e.g., `['users', 'byId', id]`.
* [x] Hooks contain only lifecycle/caching code (no business rules or mapping).
* [x] Mutations update cache via `setQueryData` and/or invalidate relevant keys.
* [x] Sensible `enabled`/staleness settings; errors are surfaced to UI (not swallowed).

## 7) Client State (store.ts) — optional

* [x] Only UI/client state lives here (no HTTP or business rules).
* [x] Selectors avoid unnecessary re-renders; state is module-scoped and namespaced.
* [x] Any persistence is intentional and minimal.

## 8) Screens & Components

* [x] Screens are **thin**: compose hooks and render DTOs; no API mapping/rules.
* [x] `components/` are reusable within this module; cross-module UI belongs in a shared `ui_system`.
* [x] Screens may compose multiple modules’ hooks for simple views; complex composition belongs in a service.

## 9) Time, Enums & Normalization

* [x] DTOs use `Date` objects (not ISO strings); mapping happens in `service.ts`.
* [x] String enums from API are narrowed to union types in DTOs.
* [x] Timezone/formatting concerns are handled in UI, not inside `service.ts`.

## 10) Typing & Contracts

* [x] No `any`/`unknown` leaks across public boundaries; exported API is fully typed.
* [x] DTO optionality reflects reality (avoid gratuitous `| null` / `| undefined`).
* [x] Public/provider functions have explicit return types (no inferred boundaries).
* [x] Discriminated unions used for multi-state results when helpful.

## 11) Tests

* [x] `test_{name}_unit.ts` exercises **non-trivial** mapping/rules in `service.ts` (edge cases, branching).
* [x] Query hooks are tested with **service mocked**; verify cache updates/invalidations for tricky flows.
* [x] No snapshot tests for trivial rendering.

## 12) Performance & Bundle Hygiene

* [x] Avoid N+1 HTTP calls; batch/parallelize (`Promise.all`) in `service.ts` when safe.
* [x] Stable hook deps; memoize selectors/expensive computations where needed.
* [x] Heavy or rarely used screens are code-split at navigation boundaries.

## 13) Error Handling & Validation

* [x] Light validation/coercion of API results at `service.ts` boundary; never trust wire types blindly.
* [x] User-facing errors are friendly; technical details go to logs/telemetry only.
* [x] Retries/backoff are intentional and bounded; idempotent mutations considered.

## 14) Security & Privacy

* [x] No secrets in client code; tokens injected via app infra and attached only in `repo.ts`.
* [x] Authorization is not trusted client-side; client checks are UX only.
* [x] PII is neither logged nor stored unnecessarily.

## 15) Observability

* [x] Structured telemetry for key flows; event names and payloads are typed.
* [x] Error boundaries exist at appropriate UI layers.

## 16) YAGNI & Dead Code

* [x] No `public`/`repo`/`nav`/`queries`/`store` if there is no **current** consumer.
* [x] Public interface remains minimal; no “just in case” methods.
* [x] Unused components/hooks/exports are removed.

## 17) Navigation (if present)

* [x] `nav.tsx` exists only when this module owns navigation; route params are typed (`{Name}StackParamList`).
* [x] Deep-link params validated at screen entry.

## 18) Styling, A11y, i18n

* [x] Components use the shared design system where applicable.
* [x] Basic accessibility (labels, roles, hit targets) is respected.

## 19) Lint & Conventions

* [x] ESLint/TS rules enforce import boundaries (e.g., no `repo` import outside `service.ts`).
* [x] Path alias `@/modules/...` is used for cross-module imports; relative paths for intra-module imports.
* [x] Prettier/formatting is consistent; CI runs `lint` and the **grep checks** below.

---

## Quick Hygiene Greps

```bash
# Cross-boundary violations (should only import other modules' public)
grep -R "from @/modules/.*/service" mobile/modules || true
grep -R "from @/modules/.*/repo"    mobile/modules || true
grep -R "from @/modules/.*/models"  mobile/modules || true

# Self-import of own public (should be empty)
for d in mobile/modules/*; do mod=$(basename "$d"); \
  grep -R "from @/modules/${mod}/public" "$d" && echo "SELF PUBLIC IMPORT FOUND in $mod"; done

# Repo usage outside repo.ts (HTTP must live only in repo.ts)
grep -R "axios\|fetch(" mobile/modules/* | grep -v "/repo.ts" || true

# React Query usage outside queries.ts (lifecycle/caching must live only there)
grep -R "useQuery\|useMutation\|QueryClient" mobile/modules/* | grep -v "/queries.ts" || true

# Wire types leaking past service (Api* should not appear in public/queries/screens)
grep -R "Api[A-Z][A-Za-z0-9]*" \
  mobile/modules/*/public.ts \
  mobile/modules/*/queries.ts \
  mobile/modules/*/screens 2>/dev/null || true

# Public forwarders doing logic (public.ts should be thin)
grep -R "public.ts" -n mobile/modules | xargs sed -n '1,200p' | grep -nE "\bif\b|\bswitch\b|\.map\(" || true

# UI imports in service.ts (should be none)
grep -R "from 'react'\|from 'react-native'" mobile/modules/*/service.ts || true

# Repo imported by queries/screens/components (should be none)
grep -R "from './repo'" mobile/modules/*/queries.ts mobile/modules/*/screens mobile/modules/*/components 2>/dev/null || true

# Public exported internals (Service/Repo should not be exported from public.ts)
grep -R "export .*Service\|export .*Repo" mobile/modules/*/public.ts || true

# Query keys are namespaced (look for first segment equal to module name)
grep -R "queryKey:" mobile/modules/*/queries.ts | grep -v "^\s*$" || true
```
