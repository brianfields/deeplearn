# Frontend Modular Scheme (mirrors backend, services compose, local-first)

```
mobile/modules/{name}/
├── models.ts              # DTOs / view models (types only; no logic)
├── repo.ts                # HTTP access and enqueus to outbox (this module's backend routes only; returns API wire types)
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

1. **All reads are local**: UI queries always read from local storage (fast, predictable, offline-capable)
2. **All writes are local + outbox**: Writes update local storage immediately AND enqueue to outbox for eventual sync
3. **Explicit sync methods**: Separate `sync*()` methods pull data from server and update local storage
4. **No network fallbacks in reads**: Don't try network then fallback to local; just use local
5. **Generate IDs locally**: Create IDs on device (e.g., `${type}_${timestamp}_${random}`) for offline creation
6. **Outbox drains automatically**: Background process syncs pending writes when online

### Pattern: Writes

```typescript
// service.ts
async createItem(data: CreateItemRequest): Promise<Item> {
  // 1. Generate ID locally
  const itemId = this.generateId();

  // 2. Create item locally
  const item: Item = { id: itemId, ...data, createdAt: new Date().toISOString() };
  await this.storage.set(`item_${itemId}`, JSON.stringify(item));

  // 3. Add to local index for querying
  await this.addToIndex('items', itemId);

  // 4. Enqueue to outbox for server sync
  await this.outbox.enqueue({
    endpoint: '/api/v1/items',
    method: 'POST',
    payload: { ...data, item_id: itemId },
    idempotencyKey: `create-item-${itemId}`,
  });

  // 5. Return immediately - no network wait
  return item;
}
```

### Pattern: Reads

```typescript
// service.ts
async getItems(userId: string, filters?: Filters): Promise<Item[]> {
  // Always read from local storage - fast and works offline
  const itemIds = await this.getLocalIndex('items', userId);
  const items = await Promise.all(
    itemIds.map(id => this.storage.get(`item_${id}`))
  );

  // Apply filters locally
  return items
    .filter(item => item && this.matchesFilters(item, filters))
    .map(item => JSON.parse(item));
}
```

### Pattern: Sync

```typescript
// service.ts
async syncItemsFromServer(userId: string): Promise<void> {
  try {
    // Explicit sync - only called when user wants to pull updates
    const response = await this.repo.getItems(userId);

    // Update local storage with server data
    for (const item of response.items) {
      await this.storage.set(`item_${item.id}`, JSON.stringify(item));
      await this.addToIndex('items', item.id, userId);
    }

    console.info(`Synced ${response.items.length} items from server`);
  } catch (error) {
    // Sync failures are non-fatal - just log and continue
    console.warn('Sync failed:', error);
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
* **Repo** calls **only** this module's backend routes (vertical slice). DO NOT CALL ROUTES FROM MODULES THAT ARE NAMED DIFFERENTLY THAN THIS MODULE. A module is a vertical slice through both the backend and the frontend.
* **Cross-module imports:** only from `modules/{other}/public`.
* Don't add to the public API unless there's a clear need.
* Do not use 'public.ts' from within that module; 'public.ts' is only for other modules to import from. Use 'service.ts' instead (otherwise there is a circular dependency).
* **Local-first**: All user-facing operations read from local storage; sync explicitly via dedicated methods.
* **Generate IDs locally**: For offline creation, generate IDs on device (e.g., `session_${Date.now()}_${Math.random()}`).
* **Outbox for writes**: Mutations update local storage AND enqueue to outbox; don't wait for network.

### One-way arrows

```
queries.ts  →  service.ts  →  local storage (primary)
                          →  repo.ts  →  HTTP (sync only)
                          →  outbox (writes)
public.ts   →  service.ts
service.ts  →  otherModule/public   (composition)
screens/    →  thisModule/queries   (+ optionally otherModule/public hooks for simple UI composition)
```

**Local-first flow:**
- Reads: `queries.ts → service.ts → local storage → return immediately`
- Writes: `queries.ts → service.ts → local storage + outbox → return immediately`
- Sync: `syncMutation → service.sync*() → repo.ts → HTTP → local storage`

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

### repo.ts (HTTP for this module only - used for sync operations)

```ts
import axios from 'axios';
import type { ApiUser } from './models';

const MODULE_BASE = '/api/v1/users'; // only this module's routes

const http = axios.create({
  baseURL: MODULE_BASE,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
});

export const UserRepo = {
  // Note: In local-first architecture, repo is used primarily for sync operations
  // Regular reads/writes go through local storage in service.ts

  async list(params?: { role?: string }): Promise<ApiUser[]> {
    // Used by service.syncUsersFromServer() to pull updates
    const { data } = await http.get(`/users`, { params });
    return data as ApiUser[];
  },
  async promote(userId: number, newRole: string): Promise<ApiUser> {
    // Write operations - typically called by outbox processor, not directly
    const { data } = await http.post(`/users/${userId}/promote`, { new_role: newRole });
    return data as ApiUser;
  }
};
```

### service.ts (use-cases; mapping; returns DTOs; local-first)

```ts
import { UserRepo } from './repo';
import { infrastructureProvider } from '../infrastructure/public';
import { offlineCacheProvider } from '../offline_cache/public';
import type { ApiUser, User } from './models';

const toDTO = (a: ApiUser): User => {
  const createdAt = new Date(a.created_at);
  const years = (Date.now() - createdAt.getTime()) / (365 * 24 * 3600 * 1000);
  return {
    id: a.id,
    email: a.email,
    name: a.name,
    role: (a.role as User['role']) ?? 'user',
    isActive: a.is_active,
    createdAt,
    displayName: a.name,
    canPromote: a.is_active && years >= 1 && a.role !== 'admin'
  };
};

export class UserService {
  private storage = infrastructureProvider().getStorage();
  private outbox = offlineCacheProvider();

  // READ: Always from local storage (fast, works offline)
  async get(id: number): Promise<User | null> {
    const stored = await this.storage.getItem(`user_${id}`);
    return stored ? JSON.parse(stored) : null;
  }

  async list(params?: { role?: string }): Promise<User[]> {
    // Get user IDs from local index
    const indexKey = `users_index_${params?.role || 'all'}`;
    const idsJson = await this.storage.getItem(indexKey);
    const ids: number[] = idsJson ? JSON.parse(idsJson) : [];

    // Fetch users from local storage
    const users = await Promise.all(
      ids.map(async id => {
        const stored = await this.storage.getItem(`user_${id}`);
        return stored ? JSON.parse(stored) as User : null;
      })
    );

    return users.filter((u): u is User => u !== null);
  }

  // WRITE: Update local storage + enqueue to outbox (instant return)
  async promote(userId: number, newRole: string): Promise<User> {
    // Get current user
    const user = await this.get(userId);
    if (!user) throw new Error('User not found');

    // Update locally
    const updated = { ...user, role: newRole as User['role'] };
    await this.storage.setItem(`user_${userId}`, JSON.stringify(updated));

    // Enqueue to outbox for server sync
    await this.outbox.enqueueOutbox({
      endpoint: `/api/v1/users/${userId}/promote`,
      method: 'POST',
      payload: { new_role: newRole },
      headers: { 'Content-Type': 'application/json' },
      idempotencyKey: `promote-user-${userId}-${Date.now()}`,
    });

    return updated;
  }

  // SYNC: Explicit method to pull from server and update local storage
  async syncUsersFromServer(params?: { role?: string }): Promise<void> {
    try {
      const apiUsers = await UserRepo.list(params);

      // Update local storage with server data
      for (const apiUser of apiUsers) {
        const user = toDTO(apiUser);
        await this.storage.setItem(`user_${user.id}`, JSON.stringify(user));
        await this.addToIndex(user, params?.role);
      }

      console.info(`Synced ${apiUsers.length} users from server`);
    } catch (error) {
      console.warn('Failed to sync users:', error);
      // Non-fatal - app continues working with local data
    }
  }

  private async addToIndex(user: User, role?: string): Promise<void> {
    const indexKey = `users_index_${role || 'all'}`;
    const idsJson = await this.storage.getItem(indexKey);
    const ids: number[] = idsJson ? JSON.parse(idsJson) : [];
    if (!ids.includes(user.id)) {
      ids.push(user.id);
      await this.storage.setItem(indexKey, JSON.stringify(ids));
    }
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
