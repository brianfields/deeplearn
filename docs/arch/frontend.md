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

### Rules for Local-First

1. **All reads are local**: UI queries always read from local storage via repo helpers (fast, predictable, offline-capable)
2. **All writes are local + outbox**: Repo methods persist to AsyncStorage AND enqueue to outbox for eventual sync
3. **Explicit sync methods live in repo**: `repo.sync*FromServer()` pulls data from HTTP and updates local storage/indexes
4. **Service never touches infrastructure/offline cache/outbox directly**: It only calls repo methods
5. **Generate IDs locally**: Create IDs on device (e.g., `${type}_${timestamp}_${random}`) for offline creation
6. **Outbox drains automatically**: Background process syncs pending writes when online (repo enqueues the payloads)

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
                                   ↘︎   HTTP (sync-only sync* calls)
public.ts   →  service.ts
service.ts  →  otherModule/public   (composition)
screens/    →  thisModule/queries   (+ optionally otherModule/public hooks for simple UI composition)
```

**Local-first flow:**
- Reads: `queries.ts → service.ts → repo.ts → local storage/offline cache → return immediately`
- Writes: `queries.ts → service.ts → repo.ts → local storage + outbox → return immediately`
- Sync: `syncMutation → service.sync*() → repo.ts.sync*FromServer() → HTTP → local storage`

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

## Local-First Best Practices

1. **ID Generation**: Use `${type}_${Date.now()}_${Math.random().toString(36).slice(2)}` for offline creation
2. **Maintain indices**: Store arrays of IDs for efficient querying (e.g., `users_index_all`)
3. **Sync on app start**: Background sync in `useEffect` - doesn't block UI
4. **Outbox drains automatically**: Use `offline_cache` module's outbox pattern
5. **Non-fatal sync failures**: Log sync errors but don't break the app
6. **Cache invalidation**: After sync, invalidate queries to refetch from updated local storage
7. **Optimistic UI**: Update local storage immediately, UI reflects changes instantly

## "Don't create files you don't need"

* No backend API? Omit `repo.ts` and `queries.ts`.
* No navigation? Omit `nav.tsx`.
* Keep the slice lean; add files only when a concrete need appears.
* If fully local (no sync needed), omit `repo.ts` entirely.
