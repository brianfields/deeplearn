# Frontend Modular Scheme (mirrors backend, services compose, local-first)

```
mobile/modules/{name}/
├── models.ts              # DTOs / view models (types only; no logic)
├── repo.ts                # Data access: AsyncStorage, offline cache, outbox, HTTP (module routes only; returns API wire types)
├── service.ts             # Use-cases; API→DTO mapping; business rules; returns DTOs only
├── public.ts              # Narrow contract: selects/forwards service methods (no logic)
├── queries.ts             # React Query hooks that call THIS module's service (cache & lifecycle only)
├── store.ts               # Client state (Zustand/Jotai) — first-class, module-local
├── nav.tsx                # Module navigator (stack)
├── screens/               # Thin UI; intra-module can import internals
├── components/            # Reusable components for within this module only (if general component that is shared across modules, it should be in the ui_system module)
└── test_{name}_unit.ts   # Unit tests for this module
```

## Local-First Architecture (Critical)

**Core Principle**: The app works offline-first. All user-facing operations use local storage; network sync happens explicitly and in the background.

### Offline vs Online: When to Use Each

Not all features need to be offline-capable. Use this decision tree:

#### ✅ **Offline-First (Cache + Sync + Outbox)** - Use when:
- User needs to access previously synced data without network
- Data is user-specific (My Units, downloaded lessons, session history)
- Mutations can be queued for later (create notes, add favorites, draft edits)
- **Read Pattern**: Read from cache → Return immediately. Background sync updates cache.
- **Write Pattern**: Write to local storage + enqueue to outbox → Return immediately. Outbox drains when online.
- **Example**: `getUserUnitCollections()` reads from offline cache; `createNote()` writes to local + outbox.

#### 🌐 **Online-Only (Direct Server Calls)** - Use when:
- Data changes frequently across devices (global catalog, shared content)
- User expects fresh data (browsing, search)
- Data is public/not personalized
- Mutations require immediate server validation (remove from collection, publish action)
- **Read Pattern**: Fetch from server → Return fresh data. No caching.
- **Write Pattern**: Direct API call → Update server → Optionally trigger sync to refresh cache.
- **Example**: `browseCatalogUnits()` fetches fresh; `removeUnitFromMyUnits()` calls API directly.

#### 💾 **Hybrid (Cache + Fresh Fetch)** - Use when:
- User needs offline access to specific items (downloaded lessons)
- Fresh data is preferred when online
- **Pattern**: Try cache first → If missing or stale, fetch from server → Cache result.
- **Example**: `getUnitDetail()` checks cache; if not downloaded, syncs from server.

### Real-World Examples from Content Module

```typescript
// ✅ OFFLINE: My Units (user-specific, cached)
async getUserUnitCollections(userId: number): Promise<UserUnitCollections> {
  // Reads from offline cache populated by sync endpoint
  const cached = await this.ensureUnitsCached();
  // Filter for units owned by user or in their My Units (synced periodically)
  return this.filterAndMapCached(cached, userId);
}

// 🌐 ONLINE: Catalog Browsing (fresh, global)
async browseCatalogUnits(): Promise<Unit[]> {
  // Always fetch fresh from server - catalog changes frequently
  const apiUnits = await this.repo.listUnits();
  return apiUnits.map(toDTO);
}

// 💾 HYBRID: Unit Detail (cache for downloaded, fetch for new)
async getUnitDetail(unitId: string): Promise<UnitDetail | null> {
  let cached = await this.offlineCache.getUnitDetail(unitId);
  if (!cached) {
    await this.runSyncCycle(); // Fetch from server if not cached
    cached = await this.offlineCache.getUnitDetail(unitId);
  }
  return cached ? this.mapToDTO(cached) : null;
}

// ✅ OFFLINE MUTATION: Create Note (works offline via outbox)
async createNote(userId: number, unitId: string, text: string): Promise<Note> {
  const noteId = this.generateId();
  const note: Note = { id: noteId, userId, unitId, text, createdAt: new Date() };

  // Save to local storage immediately - UI updates instantly
  await this.repo.saveLocalNote(note);
  // Enqueue to outbox - syncs to server when online
  await this.repo.enqueueCreateNote(note);

  return note; // Returns immediately, works offline
}

// 🌐 ONLINE MUTATION: Remove from My Units (requires network connection)
async removeUnitFromMyUnits(userId: number, unitId: string): Promise<void> {
  // This is an online-only mutation - requires immediate server response
  await this.repo.removeUnitFromMyUnits({ userId, unitId }); // Direct API call
  await this.runSyncCycle(); // Update cache - unit no longer appears in My Units
}
```

### Rules for Local-First vs Online-Only

#### Offline-First Features (use outbox):
1. **All reads are local**: UI queries read from local storage via repo helpers (fast, predictable, offline-capable)
2. **All writes use outbox**: Repo methods persist to local storage AND enqueue to outbox for eventual sync
3. **Generate IDs locally**: Create IDs on device (e.g., `${type}_${timestamp}_${random}`) for offline creation
4. **Outbox drains automatically**: Background process syncs pending writes when online
5. **User collections are offline-first**: Personal data (My Units, created content, history, notes) uses cache + sync + outbox

#### Online-Only Features (direct server calls):
1. **Reads fetch fresh**: Queries call repo methods that make direct HTTP requests (no cache)
2. **Writes call API directly**: Mutations that need immediate validation use direct API calls (not outbox)
3. **Post-mutation sync**: After successful mutation, optionally trigger sync to update cache
4. **Browsing/discovery is online-only**: Catalog, search, and shared content fetch fresh data from server

#### Universal Rules:
1. **Explicit sync methods live in repo**: `repo.sync*FromServer()` pulls data from HTTP and updates local storage/indexes
2. **Service never touches infrastructure/offline cache/outbox directly**: It only calls repo methods
3. **Repo owns the decision**: Service calls repo methods; repo decides whether to use cache/outbox or direct HTTP

### Pattern: Writes

```typescript
// service.ts
async createItem(userId: string, data: CreateItemRequest): Promise<Item> {
  const itemId = this.generateId();
  const item: Item = { id: itemId, ...data, createdAt: new Date().toISOString() };

  await this.repo.saveLocalItem(userId, item);        // Repo owns AsyncStorage keys
  await this.repo.enqueueCreateItem(item);            // Repo enqueues to outbox with idempotency key

  return item; // Returns immediately - no network wait
}
```

```typescript
// repo.ts
async saveLocalItem(userId: string, item: Item): Promise<void> {
  await this.storage.setItem(this.getItemKey(item.id), JSON.stringify(item));
  await this.addToIndex(userId, item.id);
}

async enqueueCreateItem(item: Item): Promise<void> {
  await this.outbox.enqueueOutbox({
    endpoint: '/api/v1/items',
    method: 'POST',
    payload: { ...item, created_at: item.createdAt },
    headers: { 'Content-Type': 'application/json' },
    idempotencyKey: `create-item-${item.id}`,
  });
}

private getItemKey(itemId: string): string {
  return `item_${itemId}`;
}

private getIndexKey(userId: string): string {
  return `items_index_${userId}`;
}

private async addToIndex(userId: string, itemId: string): Promise<void> {
  const indexJson = await this.storage.getItem(this.getIndexKey(userId));
  const index = indexJson ? JSON.parse(indexJson) as string[] : [];
  if (!index.includes(itemId)) {
    index.push(itemId);
    await this.storage.setItem(this.getIndexKey(userId), JSON.stringify(index));
  }
}
```

### Pattern: Reads

```typescript
// service.ts
async getItems(userId: string, filters?: Filters): Promise<Item[]> {
  return this.repo.listLocalItems(userId, filters); // Repo reads + filters locally
}
```

```typescript
// repo.ts
async listLocalItems(userId: string, filters?: Filters): Promise<Item[]> {
  const index = await this.readIndex(userId);
  const storedItems = await Promise.all(
    index.map(id => this.storage.getItem(this.getItemKey(id)))
  );

  return storedItems
    .map(json => (json ? JSON.parse(json) as Item : null))
    .filter((item): item is Item => item !== null && this.matchesFilters(item, filters));
}

private async readIndex(userId: string): Promise<string[]> {
  const indexJson = await this.storage.getItem(this.getIndexKey(userId));
  return indexJson ? JSON.parse(indexJson) : [];
}

private matchesFilters(item: Item, filters?: Filters): boolean {
  if (!filters) {
    return true;
  }
  // Apply domain-specific filters locally (still inside repo so service stays simple)
  return Object.entries(filters).every(([key, value]) => item[key as keyof Item] === value);
}
```

### Pattern: Sync

```typescript
// service.ts
async syncItemsFromServer(userId: string): Promise<void> {
  await this.repo.syncItemsFromServer(userId); // Repo orchestrates HTTP + storage writes
}
```

```typescript
// repo.ts
async syncItemsFromServer(userId: string): Promise<void> {
  const { data } = await this.http.get(`/users`, { params: { user_id: userId } });

  for (const apiItem of data.items) {
    await this.storage.setItem(this.getItemKey(apiItem.id), JSON.stringify(apiItem));
    await this.addToIndex(userId, apiItem.id);
  }
}
```

### Usage Pattern

```typescript
// On app start or explicit refresh
const { mutate: syncItems } = useSyncItems();
useEffect(() => {
  syncItems(userId); // Background sync, doesn't block UI
}, [userId]);

// Normal usage - always fast
const { data: items } = useItems(userId); // Reads from local storage
const { mutate: createItem } = useCreateItem(); // Writes to local + outbox

// User creates item
createItem(data); // Returns immediately, syncs in background
```

## Rules (same spirit as backend, plus local-first)

* **Service returns DTOs** (never wire types).
* **Public** only **selects/forwards** `service` methods (no mapping/logic).
* **Queries** are **not special**: they call **this module's service**; no business rules in hooks.
* **Cross-module composition lives in `service.ts`**, importing **other modules' `public`** only.
* **Screens** may compose multiple modules' hooks side-by-side for simple views.
* **Repo owns data access**: it wraps AsyncStorage, offline cache, outbox, and HTTP; services never import `infrastructureProvider()` or `offlineCacheProvider()` directly.
* **Sync orchestration belongs in repo**: `service.sync*()` methods delegate to `repo.sync*FromServer()` implementations.
* **Repo** calls **only** this module's backend routes (vertical slice). DO NOT CALL ROUTES FROM MODULES THAT ARE NAMED DIFFERENTLY THAN THIS MODULE. A module is a vertical slice through both the backend and the frontend.
* **Cross-module imports:** only from `modules/{other}/public`.
* Don't add to the public API unless there's a clear need.
* Do not use 'public.ts' from within that module; 'public.ts' is only for other modules to import from. Use 'service.ts' instead (otherwise there is a circular dependency).
* **Local-first**: All user-facing operations read from local storage; sync explicitly via dedicated methods.
* **Generate IDs locally**: For offline creation, generate IDs on device (e.g., `session_${Date.now()}_${Math.random()}`).
* **Outbox for writes**: Mutations update local storage AND enqueue to outbox; don't wait for network.

### One-way arrows

```
queries.ts  →  service.ts  →  repo.ts  →  local storage / offline cache (primary)
                                   ↘︎   outbox (writes)
                                   ↘︎   HTTP (direct fetches for catalog/browse)
public.ts   →  service.ts
service.ts  →  otherModule/public   (composition)
screens/    →  thisModule/queries   (+ optionally otherModule/public hooks for simple UI composition)
```

**Offline-first flow (My Units, downloaded content, user-created data):**
- Reads: `queries.ts → service.ts → repo.ts → local storage/offline cache → return immediately`
- Writes (via outbox): `queries.ts → service.ts → repo.ts → local storage + outbox.enqueue() → return immediately`
  - Background: `outbox drains → HTTP POST/PUT/DELETE → server updated`
- Sync: `syncMutation → service.sync*() → repo.ts.sync*FromServer() → HTTP GET → local storage`

**Online-only flow (Catalog, search, browsing, server-validated actions):**
- Reads: `queries.ts → service.ts → repo.ts → HTTP GET → return fresh data (no cache)`
- Writes (direct API): `queries.ts → service.ts → repo.ts → HTTP POST/DELETE → await response → trigger sync → update cache`

---

## Minimal example — `mobile/modules/users/`

### models.ts

```ts
export type UserId = number;

export interface User {
  id: UserId;
  email: string;
  name: string;
  role: 'user' | 'admin' | 'manager';
  isActive: boolean;
  createdAt: Date;
  displayName: string;   // derived
  canPromote: boolean;   // derived
}

// Shape persisted in AsyncStorage (repo-owned)
export interface StoredUser {
  id: UserId;
  email: string;
  name: string;
  role: 'user' | 'admin' | 'manager';
  isActive: boolean;
  createdAt: string; // ISO string for storage
}

// API wire format (private to module)
export interface ApiUser {
  id: number;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  created_at: string; // ISO
}
```

### repo.ts (data access: AsyncStorage + outbox + HTTP sync)

```ts
import { infrastructureProvider } from '../infrastructure/public';
import { offlineCacheProvider } from '../offline_cache/public';
import type { ApiUser, StoredUser } from './models';

const MODULE_BASE = '/api/v1/users';
const USER_INDEX_KEY = 'users/index';

export class UserRepo {
  private infrastructure = infrastructureProvider();
  private offlineCache = offlineCacheProvider();

  async getLocalUser(id: number): Promise<StoredUser | null> {
    return this.readJson<StoredUser>(this.getUserKey(id));
  }

  async listLocalUsers(params?: { role?: string }): Promise<StoredUser[]> {
    const ids = (await this.readJson<number[]>(this.getIndexKey(params?.role))) ?? [];
    const users: StoredUser[] = [];
    for (const userId of ids) {
      const user = await this.getLocalUser(userId);
      if (user) {
        users.push(user);
      }
    }
    return users;
  }

  async saveLocalUser(user: StoredUser, role?: string): Promise<void> {
    await this.writeJson(this.getUserKey(user.id), user);
    await this.addToIndex(user.id);
    if (role) {
      await this.addToIndex(user.id, role);
    }
  }

  async enqueuePromotion(userId: number, newRole: string): Promise<void> {
    await this.offlineCache.enqueueOutbox({
      endpoint: `${MODULE_BASE}/${userId}/promote`,
      method: 'POST',
      payload: { new_role: newRole },
      headers: { 'Content-Type': 'application/json' },
      idempotencyKey: `promote-user-${userId}`,
    });
  }

  async syncUsersFromServer(params?: { role?: string }): Promise<void> {
    const query = params?.role ? `?role=${encodeURIComponent(params.role)}` : '';
    const apiUsers = await this.infrastructure.request<ApiUser[]>(`${MODULE_BASE}/users${query}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    for (const apiUser of apiUsers) {
      const stored = this.mapApiUser(apiUser);
      await this.saveLocalUser(stored, stored.role);
    }
  }

  private getUserKey(id: number): string {
    return `users/user/${id}`;
  }

  private getIndexKey(role?: string): string {
    return role ? `${USER_INDEX_KEY}/${role}` : USER_INDEX_KEY;
  }

  private async addToIndex(id: number, role?: string): Promise<void> {
    const key = this.getIndexKey(role);
    const existing = (await this.readJson<number[]>(key)) ?? [];
    if (!existing.includes(id)) {
      existing.push(id);
      await this.writeJson(key, existing);
    }
  }

  private async readJson<T>(key: string): Promise<T | null> {
    const stored = await this.infrastructure.getStorageItem(key);
    return stored ? (JSON.parse(stored) as T) : null;
  }

  private async writeJson<T>(key: string, value: T): Promise<void> {
    await this.infrastructure.setStorageItem(key, JSON.stringify(value));
  }

  private mapApiUser(api: ApiUser): StoredUser {
    return {
      id: api.id,
      email: api.email,
      name: api.name,
      role: (api.role as StoredUser['role']) ?? 'user',
      isActive: api.is_active,
      createdAt: api.created_at,
    };
  }
}

export function userRepo(): UserRepo {
  return new UserRepo();
}
```

### service.ts (business logic + DTO mapping; repo handles storage & outbox)

```ts
import { userRepo } from './repo';
import type { StoredUser, User } from './models';

export class UserService {
  constructor(private repo = userRepo()) {}

  async get(id: number): Promise<User | null> {
    const stored = await this.repo.getLocalUser(id);
    return stored ? this.toDTO(stored) : null;
  }

  async list(params?: { role?: string }): Promise<User[]> {
    const storedUsers = await this.repo.listLocalUsers(params);
    return storedUsers.map(u => this.toDTO(u));
  }

  async promote(userId: number, newRole: string): Promise<User> {
    const current = await this.get(userId);
    if (!current) {
      throw new Error('User not found');
    }

    const updated: User = { ...current, role: newRole as User['role'] };
    await this.repo.saveLocalUser(this.fromDTO(updated), updated.role);
    await this.repo.enqueuePromotion(userId, newRole);

    return updated;
  }

  async syncUsersFromServer(params?: { role?: string }): Promise<void> {
    await this.repo.syncUsersFromServer(params);
  }

  private toDTO(stored: StoredUser): User {
    const createdAt = new Date(stored.createdAt);
    const years = (Date.now() - createdAt.getTime()) / (365 * 24 * 3600 * 1000);
    return {
      id: stored.id,
      email: stored.email,
      name: stored.name,
      role: stored.role,
      isActive: stored.isActive,
      createdAt,
      displayName: stored.name,
      canPromote: stored.isActive && years >= 1 && stored.role !== 'admin',
    };
  }

  private fromDTO(user: User): StoredUser {
    return {
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
      isActive: user.isActive,
      createdAt: user.createdAt.toISOString(),
    };
  }
}
```

> **Cross-module composition example (in a different module’s `service.ts`)**
>
> ```ts
> // modules/dashboard/service.ts
> import { usersProvider } from '@/modules/users/public';
> import { ordersProvider } from '@/modules/orders/public';
>
> export class DashboardService {
>   constructor(
>     private users = usersProvider(),
>     private orders = ordersProvider()
>   ) {}
>   async userOverview(userId: number) {
>     const [u, os] = await Promise.all([this.users.get(userId), this.orders.byUser(userId)]);
>     return { user: u, orderCount: os.length };
>   }
> }
> ```

### public.ts (pure forwarder, like backend)

```ts
import { UserService } from './service';
import type { User } from './models';

export interface UsersProvider {
  get(id: number): Promise<User | null>;
  list(params?: { role?: string }): Promise<User[]>;
  promote(userId: number, newRole: string): Promise<User>;
}

export function usersProvider(): UsersProvider {
  const svc = new UserService();
  return {
    get: svc.get.bind(svc),
    list: svc.list.bind(svc),
    promote: svc.promote.bind(svc)
  };
}

export type { User } from './models';
```

### queries.ts (React Query; **calls service**; local-first)

```ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { UserService } from './service';
import type { User } from './models';

const svc = new UserService();

export const qk = {
  user: (id: number) => ['users', 'byId', id] as const,
  list: (p?: object) => ['users', 'list', p ?? {}] as const,
};

// READS: Always from local storage (fast, works offline)
export function useUser(id: number) {
  return useQuery({
    queryKey: qk.user(id),
    queryFn: () => svc.get(id), // Reads from local storage
    enabled: !!id,
    staleTime: Infinity, // Local data doesn't go stale until we sync
  });
}

export function useUsers(params?: { role?: string }) {
  return useQuery({
    queryKey: qk.list(params),
    queryFn: () => svc.list(params), // Reads from local storage
    staleTime: Infinity, // Local data doesn't go stale until we sync
  });
}

// WRITE: Updates local + enqueues to outbox (instant)
export function usePromoteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: { userId: number; newRole: string }) =>
      svc.promote(p.userId, p.newRole), // Updates local + outbox
    onSuccess: (dto: User) => {
      // Optimistically update cache (data is already in local storage)
      qc.setQueryData(qk.user(dto.id), dto);
      qc.invalidateQueries({ queryKey: qk.list() });
    }
  });
}

// SYNC: Explicit pull from server (call on app start or user request)
export function useSyncUsers() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params?: { role?: string }) =>
      svc.syncUsersFromServer(params), // Pulls from server → updates local
    onSuccess: () => {
      // Invalidate to refetch from updated local storage
      qc.invalidateQueries({ queryKey: ['users'] });
    }
  });
}
```

> **If you need per-call DI (e.g., token/locale):** create a tiny local factory in `queries.ts` that builds `new UserService(deps)` and use that.

### store.ts (client state; first-class)

```ts
import { create } from 'zustand';

type State = { viewMode: 'list' | 'detail'; selectedId: number | null; favoriteIds: number[] };
type Actions = {
  setViewMode(v: State['viewMode']): void;
  select(id: number | null): void;
  toggleFavorite(id: number): void;
};

export const useUserStore = create<State & Actions>((set, get) => ({
  viewMode: 'list',
  selectedId: null,
  favoriteIds: [],
  setViewMode: (v) => set({ viewMode: v }),
  select: (id) => set({ selectedId: id }),
  toggleFavorite: (id) => {
    const { favoriteIds } = get();
    set({
      favoriteIds: favoriteIds.includes(id)
        ? favoriteIds.filter(x => x !== id)
        : [...favoriteIds, id]
    });
  }
}));
```

### nav.tsx (module navigator)
```tsx
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { UserProfileScreen } from './screens/UserProfileScreen';

export type UserStackParamList = { UserProfile: { userId: number } };
const Stack = createNativeStackNavigator<UserStackParamList>();

export function UserNav() {
  return (
    <Stack.Navigator initialRouteName="UserProfile">
      <Stack.Screen name="UserProfile" component={UserProfileScreen} />
    </Stack.Navigator>
  );
}
```

### screens/UserProfileScreen.tsx (thin UI; local-first means instant)
```tsx
import { Text, Button, View } from 'react-native';
import { useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { UserStackParamList } from '../nav';
import { useUser, usePromoteUser, useSyncUsers } from '../queries';
import { useUserStore } from '../store';
import { useEffect } from 'react';

export function UserProfileScreen() {
  const { params: { userId } } = useRoute<RouteProp<UserStackParamList, 'UserProfile'>>();
  const { data: user, isPending, error } = useUser(userId); // Reads from local storage
  const promote = usePromoteUser(); // Writes to local + outbox
  const syncUsers = useSyncUsers(); // Explicit sync from server
  const toggleFavorite = useUserStore(s => s.toggleFavorite);

  // Optional: Sync in background on mount (doesn't block UI)
  useEffect(() => {
    syncUsers.mutate();
  }, []);

  if (isPending) return <Text>Loading…</Text>; // Fast - local storage only
  if (error || !user) return <Text>Not found</Text>;

  return (
    <View>
      <Text>{user.displayName}</Text>
      <Text>{user.email}</Text>
      <Button title="★ Favorite" onPress={() => toggleFavorite(user.id)} />
      {user.canPromote && (
        <Button
          title="Promote to manager"
          onPress={() => promote.mutate({ userId, newRole: 'manager' })} // Instant response
        />
      )}
      <Button
        title="↻ Refresh from server"
        onPress={() => syncUsers.mutate()}
      />
    </View>
  );
}
```

---

## Import policy (crisp)

* **Cross-module:** import **only** from `@/modules/{other}/public`.
* **Inside a module:** screens/components/hooks may import `service`, `queries`, `store`, etc.
* **Only `service.ts` may import `repo.ts`.**
* **Only `service.ts` or screens may import other modules’ `public`.**

---

## React Query conventions

* **Keys**: prefix with module (`['users', ...]`).
* **Hooks**: call **service** only; no API mapping or rules in hooks.
* **Optimistic updates**: in `queries.ts` via `setQueryData`; the real write goes through `service`.
* **Prefetch**: `queryClient.prefetchQuery` with the same keys.
* **Defaults**: set `staleTime/gcTime` app-wide; override per-hook when needed.

---

## Testing (minimal but meaningful)

* Minimal unit tests for complex functionality in service.ts only. No need to test simple getters, API mapping, etc.

---

## Offline/Online Best Practices

### When to Cache (Offline-First with Outbox)
1. **User-specific data**: Personal collections, created content, session history
2. **Downloaded content**: Lessons, media files explicitly downloaded for offline use
3. **Mutations use outbox**: Create, update, delete operations enqueue to outbox (work offline)
4. **ID Generation**: Use `${type}_${Date.now()}_${Math.random().toString(36).slice(2)}` for offline creation
5. **Maintain indices**: Store arrays of IDs for efficient querying (e.g., `users_index_all`)
6. **Sync on app start**: Background sync in `useEffect` - doesn't block UI
7. **Non-fatal sync failures**: Log sync errors but don't break the app
8. **Optimistic UI**: Update local storage immediately, UI reflects changes instantly
9. **Example mutations**: Create notes, add favorites, draft edits, toggle settings

### When to Fetch Fresh (Online-Only with Direct API Calls)
1. **Catalog/browsing**: Global content that changes across devices
2. **Search results**: Real-time queries that should reflect latest state
3. **Shared/public data**: Content not owned by user
4. **No offline requirement**: Features that don't need to work without network
5. **Mutations require validation**: Remove from collection, publish actions call API directly (not outbox)
6. **Direct API calls**: Use `repo` methods that make HTTP requests and return fresh data
7. **Example mutations**: Remove from My Units, subscribe to unit, report content

### Sync Strategy
- **User collections sync with `user_id`**: Backend filters to owned + subscribed items
- **Periodic background sync**: Keep cache fresh without blocking UI
- **Post-mutation sync**: After add/remove operations, trigger sync to update cache
- **Cache invalidation**: After sync, invalidate React Query cache to refetch from updated storage

## "Don't create files you don't need"

* No backend API? Omit `repo.ts` and `queries.ts`.
* No navigation? Omit `nav.tsx`.
* Keep the slice lean; add files only when a concrete need appears.
* If fully local (no sync needed), omit `repo.ts` entirely.
