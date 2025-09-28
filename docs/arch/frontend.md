# Frontend Modular Scheme (mirrors backend, services compose)

```
mobile/modules/{name}/
├── models.ts              # DTOs / view models (types only; no logic)
├── repo.ts                # HTTP access (this module’s backend routes only; returns API wire types)
├── service.ts             # Use-cases; API→DTO mapping; business rules; returns DTOs only
├── public.ts              # Narrow contract: selects/forwards service methods (no logic)
├── queries.ts             # React Query hooks that call THIS module's service (cache & lifecycle only)
├── store.ts               # Client state (Zustand/Jotai) — first-class, module-local
├── nav.tsx                # Module navigator (stack)
├── screens/               # Thin UI; intra-module can import internals
├── components/            # Reusable components for within this module only (if general component that is shared across modules, it should be in the ui_system module)
└── test_{name}_unit.ts   # Unit tests for this module
```

## Rules (same spirit as backend)

* **Service returns DTOs** (never wire types).
* **Public** only **selects/forwards** `service` methods (no mapping/logic).
* **Queries** are **not special**: they call **this module’s service**; no business rules in hooks.
* **Cross-module composition lives in `service.ts`**, importing **other modules’ `public`** only.
* **Screens** may compose multiple modules’ hooks side-by-side for simple views.
* **Repo** calls **only** this module’s backend routes (vertical slice). DO NOT CALL ROUTES FROM MODULES THAT ARE NAMED DIFFERENTLY THAN THIS MODULE. A module is a vertical slice through both the backend and the frontend.
* **Cross-module imports:** only from `modules/{other}/public`.
* Don’t add to the public API unless there’s a clear need.
* Do not use 'public.ts' from within that module; 'public.ts' is only for other modules to import from. Use 'service.ts' instead (otherwise there is a circular dependency).

### One-way arrows

```
queries.ts  →  service.ts  →  repo.ts  →  HTTP
public.ts   →  service.ts
service.ts  →  otherModule/public   (composition)
screens/    →  thisModule/queries   (+ optionally otherModule/public hooks for simple UI composition)
```

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

### repo.ts (HTTP for this module only)

```ts
import axios from 'axios';
import type { ApiUser } from './models';

const MODULE_BASE = '/api/v1/users'; // only this module’s routes

const http = axios.create({
  baseURL: MODULE_BASE,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
});

export const UserRepo = {
  async byId(id: number): Promise<ApiUser> {
    const { data } = await http.get(`/users/${id}`);
    return data as ApiUser;
  },
  async list(params?: { role?: string }): Promise<ApiUser[]> {
    const { data } = await http.get(`/users`, { params });
    return data as ApiUser[];
  },
  async promote(userId: number, newRole: string): Promise<ApiUser> {
    const { data } = await http.post(`/users/${userId}/promote`, { new_role: newRole });
    return data as ApiUser;
  }
};
```

### service.ts (use-cases; mapping; returns DTOs; can compose other modules)

```ts
import { UserRepo } from './repo';
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
  async get(id: number): Promise<User | null> {
    try { return toDTO(await UserRepo.byId(id)); } catch { return null; }
  }
  async list(params?: { role?: string }): Promise<User[]> {
    const arr = await UserRepo.list(params);
    return arr.map(toDTO);
  }
  async promote(userId: number, newRole: string): Promise<User> {
    return toDTO(await UserRepo.promote(userId, newRole));
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

### queries.ts (React Query; **calls service**)

```ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { UserService } from './service';
import type { User } from './models';

const svc = new UserService(); // simple default; swap to a factory if you need DI

export const qk = {
  user: (id: number) => ['users', 'byId', id] as const,
  list: (p?: object) => ['users', 'list', p ?? {}] as const,
};

export function useUser(id: number) {
  return useQuery({
    queryKey: qk.user(id),
    queryFn: () => svc.get(id),
    enabled: !!id
  });
}

export function useUsers(params?: { role?: string }) {
  return useQuery({
    queryKey: qk.list(params),
    queryFn: () => svc.list(params)
  });
}

export function usePromoteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: { userId: number; newRole: string }) => svc.promote(p.userId, p.newRole),
    onSuccess: (dto: User) => {
      qc.setQueryData(qk.user(dto.id), dto);
      qc.invalidateQueries({ queryKey: qk.list() });
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

### screens/UserProfileScreen.tsx (thin UI)
```tsx
import { Text, Button, View } from 'react-native';
import { useRoute } from '@react-navigation/native';
import type { RouteProp } from '@react-navigation/native';
import type { UserStackParamList } from '../nav';
import { useUser, usePromoteUser } from '../queries';
import { useUserStore } from '../store';

export function UserProfileScreen() {
  const { params: { userId } } = useRoute<RouteProp<UserStackParamList, 'UserProfile'>>();
  const { data: user, isPending, error } = useUser(userId);
  const promote = usePromoteUser();
  const toggleFavorite = useUserStore(s => s.toggleFavorite);

  if (isPending) return <Text>Loading…</Text>;
  if (error || !user) return <Text>Not found</Text>;

  return (
    <View>
      <Text>{user.displayName}</Text>
      <Text>{user.email}</Text>
      <Button title="★ Favorite" onPress={() => toggleFavorite(user.id)} />
      {user.canPromote && (
        <Button title="Promote to manager"
                onPress={() => promote.mutate({ userId, newRole: 'manager' })} />
      )}
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

## “Don’t create files you don’t need”

* No backend API? Omit `repo.ts` and `queries.ts`.
* No navigation? Omit `nav.tsx`.
* Keep the slice lean; add files only when a concrete need appears.
