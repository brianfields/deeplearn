# Frontend Modular Architecture Cheat Sheet (React Native)

## 🎯 Core Concept for Frontend
Each module is a **frontend domain unit** with clear APIs:
- **`module_api/`** - Public interface for other frontend modules
- **`http_client/`** - Internal HTTP API for backend communication within module only
- **`screens/`** - UI presentation layer
- **`navigation/`** - Module-specific navigation

**Golden Rule:** Modules NEVER import from each other's `internal/`, `screens/`, or `http_client/` directories.

## 📁 Frontend Directory Structure

```
mobile/modules/{module-name}/
├── module_api/                      # Public interface for other frontend modules (thin facade)
│   ├── index.ts                    # Re-export stable hooks, store selectors, navigation & types
│   ├── queries.ts                  # Thin React Query hooks delegating to application/domain
│   ├── store.ts                    # Thin Zustand surface (public selectors/actions only)
│   ├── navigation.ts               # Cross-module navigation actions (no side effects)
│   └── types.ts                    # Shared types for other modules
├── screens/                        # Full-screen React Native components (UI only)
│   ├── {Entity}ListScreen.tsx
│   ├── {Entity}DetailScreen.tsx
│   ├── {Entity}EditScreen.tsx
│   └── index.ts
├── components/                     # Reusable UI within this module (not exported cross-module)
│   ├── {Entity}Card.tsx
│   ├── {Entity}Form.tsx
│   ├── {Entity}Header.tsx
│   └── index.ts
├── navigation/                     # Module-specific navigator
│   ├── {Module}Stack.tsx
│   ├── types.ts
│   └── index.ts
├── http_client/                    # Infrastructure: backend communication for this module only
│   ├── api.ts                      # HTTP requests to own backend
│   ├── mappers.ts                  # API ↔ domain mapping
│   └── types.ts                    # API-specific types
├── adapters/                       # Infrastructure: other side-effect adapters (internal)
│   ├── analytics.adapter.ts
│   ├── notifications.adapter.ts
│   └── storage.adapter.ts
├── application/                    # Use-cases/orchestration (internal; coordinates infra + domain)
│   ├── promoteUser.usecase.ts
│   ├── loadUser.usecase.ts
│   └── index.ts
├── domain/                         # Client-side business logic (pure, no side effects)
│   ├── business-rules/
│   │   └── {entity}-rules.ts
│   ├── formatters/
│   │   └── {entity}-formatter.ts
│   ├── hooks/                      # Private helper hooks
│   │   └── use{Entity}.ts
│   ├── utils/
│   │   └── {entity}-utils.ts
│   └── styles.ts                   # Module-scoped styles (optional)
└── tests/
    ├── screens/                    # Screen tests
    ├── components/                 # Component tests
    ├── module_api/                 # Public hooks/store/navigation tests
    └── integration/                # Cross-component/module tests
```

## 🏗️ Frontend Layer Responsibilities

### 📱 Screen Layer (UI Presentation)
**Purpose:** UI rendering and user interaction only - thin presentation layer

**Responsibilities:**
- Render UI based on state
- Handle user interactions (onPress, form input)
- Local UI state (modal visibility, form state)
- Platform-specific rendering
- Navigation calls

**Should NOT contain:** HTTP calls, business logic, complex data transformation

```typescript
// /mobile/modules/users/screens/UserProfileScreen.tsx
export function UserProfileScreen() {
  const route = useRoute<UserProfileScreenRouteProp>()
  const { userId } = route.params

  // Use module API hooks - no HTTP logic here
  const { user, isLoading, error } = useUser(userId)
  const { permissions } = useUserPermissions(userId)
  const { navigateToEdit } = useUserNavigation()

  // Local UI state only
  const [showMenu, setShowMenu] = useState(false)

  // Simple event handlers - delegate to navigation/stores
  const handleEdit = () => navigateToEdit(userId)
  const handleMenuToggle = () => setShowMenu(!showMenu)

  // Pure rendering based on state
  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorView error={error} />
  if (!user) return <UserNotFound />

  return (
    <ScrollView style={styles.container}>
      <UserHeader user={user} onMenuPress={handleMenuToggle} />
      <UserDetails user={user} permissions={permissions} />
      <UserActions user={user} onEdit={handleEdit} />
    </ScrollView>
  )
}
```

### 🏪 Module API Layer (State & Navigation)
**Purpose:** Data management and cross-module interface - rich coordination layer

**Responsibilities:**
- Server state management (TanStack Query)
- Client state management (Zustand)
- Data transformation for UI
- Cross-module navigation actions
- Caching and optimization
- Side effect coordination

**Should NOT contain:** UI rendering, HTTP implementation details, platform-specific code

```typescript
// /mobile/modules/users/module_api/queries.ts
export function useUserQueries() {
  return {
    useUser: (id: number) =>
      useQuery({
        queryKey: ['user', id],
        queryFn: () => userApi.getUser(id),
        enabled: !!id,
        staleTime: 5 * 60 * 1000,
        // Transform for UI consumption
        select: (user) => ({
          ...user,
          displayName: UserFormatter.formatDisplayName(user),
          canPromote: UserBusinessRules.canBePromoted(user),
          statusColor: UserBusinessRules.getStatusColor(user.status)
        })
      }),

    usePromoteUser: () =>
      useMutation({
        mutationFn: ({ userId, newRole }: PromoteUserRequest) =>
          userApi.promoteUser(userId, newRole),
        onSuccess: (user, variables) => {
          // Coordinate side effects
          queryClient.invalidateQueries(['user', variables.userId])
          NotificationService.showSuccess(`User promoted to ${variables.newRole}`)
          AnalyticsService.track('user_promoted', variables)
        },
        onError: (error) => ErrorHandler.handlePromotionError(error)
      })
  }
}
```

```typescript
// /mobile/modules/users/module_api/store.ts
export const useUserStore = create<UserState>()(
  persist(
    (set, get) => ({
      selectedUserId: null,
      viewMode: 'list',
      filterOptions: { status: 'all', role: 'all' },
      recentlyViewedUsers: [],
      favoriteUsers: [],

      // Actions with business logic
      setSelectedUser: (id) => {
        set({ selectedUserId: id })
        if (id) {
          const { recentlyViewedUsers } = get()
          const updated = [id, ...recentlyViewedUsers.filter(uid => uid !== id)].slice(0, 10)
          set({ recentlyViewedUsers: updated })
        }
      },

      toggleFavoriteUser: (id) => {
        const { favoriteUsers } = get()
        const isCurrentlyFavorite = favoriteUsers.includes(id)

        set({
          favoriteUsers: isCurrentlyFavorite
            ? favoriteUsers.filter(uid => uid !== id)
            : [...favoriteUsers, id]
        })

        AnalyticsService.track(isCurrentlyFavorite ? 'user_unfavorited' : 'user_favorited', { userId: id })
      }
    }),
    {
      name: 'user-module-storage',
      storage: createJSONStorage(() => AsyncStorage)
    }
  )
)
```

```typescript
// /mobile/modules/users/module_api/navigation.ts
export { UserNavigationStack } from '../navigation'

export const userNavigationActions = {
  navigateToUser: (userId: number) => ({
    screen: 'UserProfile' as const,
    params: { userId }
  }),
  navigateToUserEdit: (userId: number) => ({
    screen: 'UserEdit' as const,
    params: { userId }
  })
}

// Hook for other modules to use
export function useUserNavigation() {
  const navigation = useNavigation()

  return {
    navigateToUser: (userId: number) =>
      navigation.navigate('UserModule', userNavigationActions.navigateToUser(userId)),

    navigateToUserEdit: (userId: number) =>
      navigation.navigate('UserModule', userNavigationActions.navigateToUserEdit(userId))
  }
}
```

### 🌐 HTTP Client Layer (API Communication)
**Purpose:** Backend communication within module only - thin translation layer

**Responsibilities:**
- HTTP requests to own backend only
- Request/response serialization
- API data mapping
- Network error handling
- Authentication headers

**Should NOT contain:** UI logic, business rules, cross-module communication

```typescript
// /mobile/modules/users/http_client/api.ts
// This API client is ONLY used by the user-management module
const API_BASE = '/api/v1/users'

export const userApi = {
  getUser: async (id: number): Promise<User> => {
    const response = await httpClient.get(`${API_BASE}/users/${id}`)
    return UserApiMapper.fromApi(response.data)
  },

  promoteUser: async (userId: number, newRole: string): Promise<User> => {
    const response = await httpClient.post(`${API_BASE}/users/${userId}/promote`, {
      new_role: newRole
    })
    return UserApiMapper.fromApi(response.data)
  },

  getUserPermissions: async (userId: number): Promise<UserPermissions> => {
    const response = await httpClient.get(`${API_BASE}/users/${userId}/permissions`)
    return UserPermissionMapper.fromApi(response.data)
  }
}

// Module-specific HTTP client
const httpClient = axios.create({
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})

// Add auth interceptor
httpClient.interceptors.request.use((config) => {
  const token = AuthService.getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

```typescript
// /mobile/modules/users/http_client/mappers.ts
export class UserApiMapper {
  static fromApi(apiUser: ApiUser): User {
    return {
      id: apiUser.id,
      name: apiUser.name,
      email: apiUser.email,
      role: apiUser.role,
      isActive: apiUser.is_active,
      createdAt: new Date(apiUser.created_at),
      yearsOfService: UserApiMapper.calculateYearsOfService(apiUser.created_at)
    }
  }

  static toApi(user: Partial<User>): Partial<ApiUser> {
    return {
      name: user.name,
      email: user.email,
      role: user.role,
      is_active: user.isActive
    }
  }
}
```

### 🧠 Internal Layer (Business Logic & Utils)
**Purpose:** Client-side business rules and module utilities - rich domain logic

**Responsibilities:**
- Client-side validation
- Data formatting for UI
- Business rule calculations
- Offline behavior logic
- Complex data transformations

**Should NOT contain:** HTTP concerns, cross-module logic, UI rendering

```typescript
// /mobile/modules/users/internal/business-rules/user-business-rules.ts
export class UserBusinessRules {
  static canBePromoted(user: User): boolean {
    if (!user.isActive) return false
    if (user.yearsOfService < 1) return false
    if (user.performanceScore < 75) return false

    const promotionPaths = {
      'intern': ['junior'],
      'junior': ['senior', 'specialist'],
      'senior': ['lead', 'manager']
    }

    return promotionPaths[user.role]?.length > 0
  }

  static getStatusColor(status: string): string {
    const statusColors = {
      'active': '#28a745',
      'inactive': '#6c757d',
      'pending': '#ffc107',
      'suspended': '#dc3545'
    }
    return statusColors[status] || '#6c757d'
  }

  static calculateEngagementScore(user: User): number {
    let score = 0
    score += user.loginFrequency * 10
    score += user.featureUsageCount * 5

    const daysSinceLastActivity = daysBetween(new Date(), new Date(user.lastActivityAt))
    score -= daysSinceLastActivity * 2

    return Math.max(0, Math.min(100, score))
  }
}
```

```typescript
// /mobile/modules/users/internal/formatters/user-formatter.ts
export class UserFormatter {
  static formatDisplayName(user: User): string {
    return user.preferredName ? `${user.preferredName} (${user.name})` : user.name
  }

  static formatRole(role: string): string {
    const roleLabels = {
      'senior_manager': 'Senior Manager',
      'team_lead': 'Team Lead'
    }
    return roleLabels[role] || role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  static formatYearsOfService(years: number): string {
    if (years < 1) {
      const months = Math.floor(years * 12)
      return `${months} month${months !== 1 ? 's' : ''}`
    }
    return `${Math.floor(years)} year${Math.floor(years) !== 1 ? 's' : ''}`
  }
}
```

## 🔄 Layer Interfaces & Data Flow

### Data Flow Pattern:
```
User Interaction → Screen → Module API → HTTP Client → Backend
        ↓            ↓         ↓           ↓
    Touch/Press  UI State  React Query  HTTP Request
        ↑            ↑         ↑           ↑
User Feedback ← Screen ← Module API ← HTTP Client ← Backend
```

### Interface Contracts:

**Screen ↔ Module API:**
```typescript
// Screens use hooks, never direct API calls
const { user, isLoading } = useUser(userId)  // From module API
const { navigateToEdit } = useUserNavigation()  // From module API
```

**Module API ↔ HTTP Client:**
```typescript
// Module API calls HTTP client, transforms data
queryFn: () => userApi.getUser(id),  // HTTP client call
select: (user) => UserFormatter.formatDisplayName(user)  // Transform for UI
```

**Module API ↔ Internal:**
```typescript
// Module API uses internal business rules and formatters
const canPromote = UserBusinessRules.canBePromoted(user)  // Business logic
const displayName = UserFormatter.formatDisplayName(user)  // Formatting
```

## 🎯 Frontend Complexity Distribution

**✅ Correct Complexity:**
- **Screen Layer:** 25% (UI rendering only)
- **Module API:** 40% (State management & coordination)
- **HTTP Client:** 15% (Network communication)
- **Internal:** 20% (Business rules & formatting)

**❌ Anti-pattern (Fat Components):**
- **Screen Layer:** 70% ← Problem!
- **Module API:** 20%
- **HTTP Client:** 5%
- **Internal:** 5%

## 📱 Navigation Structure

### Module Navigation Stack
```typescript
// /mobile/modules/users/navigation/UserStack.tsx
import { createNativeStackNavigator } from '@react-navigation/native-stack'
import { UserListScreen, UserProfileScreen, UserEditScreen } from '../screens'

const Stack = createNativeStackNavigator<UserStackParamList>()

export function UserNavigationStack() {
  return (
    <Stack.Navigator initialRouteName="UserList">
      <Stack.Screen name="UserList" component={UserListScreen} />
      <Stack.Screen name="UserProfile" component={UserProfileScreen} />
      <Stack.Screen name="UserEdit" component={UserEditScreen} />
    </Stack.Navigator>
  )
}
```

### App-Level Navigation
```typescript
// /mobile/navigation/AppNavigator.tsx
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs'
import { UserNavigationStack } from '../modules/users'
import { OrderNavigationStack } from '../modules/orders'

const Tab = createBottomTabNavigator()

export function AppNavigator() {
  return (
    <Tab.Navigator>
      <Tab.Screen name="UserModule" component={UserNavigationStack} />
      <Tab.Screen name="OrderModule" component={OrderNavigationStack} />
    </Tab.Navigator>
  )
}
```

## 🔗 Cross-Module Communication

### ✅ Correct Way
```typescript
// Other modules use external module API only
import { useUserQueries, useUserNavigation } from '@/modules/users'

function OrderFormScreen() {
  const { useUsersByRole } = useUserQueries()  // External API
  const { navigateToUser } = useUserNavigation()  // External API
  const { data: salesReps } = useUsersByRole('sales')

  return (
    <Picker>
      {salesReps?.map(user => (
        <Picker.Item
          key={user.id}
          label={user.name}
          onPress={() => navigateToUser(user.id)}  // Cross-module navigation
        />
      ))}
    </Picker>
  )
}
```

### ❌ Wrong Ways
```typescript
// DON'T: Import from internal directories
import { UserCard } from '../users/components/UserCard'  // WRONG!
import { userApi } from '../users/http_client/api'  // WRONG!

// DON'T: Direct HTTP calls to other modules' endpoints
fetch('/api/v1/users/users/123')  // WRONG!

// DON'T: Import screens from other modules
import { UserProfileScreen } from '../users/screens/UserProfileScreen'  // WRONG!
```

## 🧪 Testing Patterns

### Screen Tests (UI Behavior)
```typescript
// /mobile/modules/users/tests/screens/UserProfileScreen.test.tsx
const mockUser = { id: 1, name: 'John Doe', role: 'manager' }

jest.mock('../../module_api', () => ({
  useUserQueries: () => ({
    useUser: () => ({ data: mockUser, isLoading: false, error: null })
  }),
  useUserNavigation: () => ({
    navigateToEdit: jest.fn()
  })
}))

describe('UserProfileScreen', () => {
  it('renders user information', () => {
    render(<UserProfileScreen />, { wrapper: TestWrapper })

    expect(screen.getByText('John Doe')).toBeTruthy()
    expect(screen.getByText('manager')).toBeTruthy()
  })
})
```

### Module API Tests (Hooks & State)
```typescript
// /mobile/modules/users/tests/module_api/queries.test.tsx
jest.mock('../http_client/api')

describe('useUserQueries', () => {
  it('should fetch and transform user data', async () => {
    const mockApiUser = { id: 1, name: 'John', is_active: true }
    userApi.getUser.mockResolvedValue(mockApiUser)

    const { result } = renderHook(() => useUserQueries().useUser(1), {
      wrapper: QueryWrapper
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data.displayName).toBe('John')
  })
})
```

### Integration Tests (Cross-Module)
```typescript
// /mobile/modules/orders/tests/integration/user-integration.test.tsx
import { useUserQueries } from '@/modules/users'

describe('Order-User Integration', () => {
  it('should load users for order assignment', async () => {
    render(<OrderFormScreen />, { wrapper: TestWrapper })

    await waitFor(() => {
      expect(screen.getByText('John Doe (Sales)')).toBeTruthy()
    })
  })
})
```

## 📋 Quick Implementation Checklist

### Creating a New Frontend Module:

1. **Setup Structure:**
   - [ ] Create module directory: `mobile/modules/{module-name}/`
   - [ ] Create subdirectories: `module_api/`, `screens/`, `components/`, `navigation/`, `http_client/`, `internal/`

2. **Implement Module API:**
   - [ ] Create TanStack Query hooks in `module_api/queries.ts`
   - [ ] Create Zustand store in `module_api/store.ts`
   - [ ] Create navigation actions in `module_api/navigation.ts`
   - [ ] Export all in `module_api/index.ts`

3. **Implement Screens:**
   - [ ] Create screens in `screens/` directory
   - [ ] Keep screens thin - only UI rendering and local state
   - [ ] Use module API hooks for data

4. **Implement Navigation:**
   - [ ] Create navigation stack in `navigation/{Module}Stack.tsx`
   - [ ] Define param types in `navigation/types.ts`
   - [ ] Add to app-level navigation

5. **Implement HTTP Client:**
   - [ ] Create API functions in `http_client/api.ts`
   - [ ] Create data mappers in `http_client/mappers.ts`
   - [ ] Handle module-specific API concerns

6. **Implement Internal Logic:**
   - [ ] Create business rules in `internal/business-rules/`
   - [ ] Create formatters in `internal/formatters/`
   - [ ] Create services for side effects in `internal/services/`

7. **Add Tests:**
   - [ ] Test screens with mocked module API
   - [ ] Test module API hooks with mocked HTTP client
   - [ ] Test cross-module integration

### Using Another Module:
```typescript
// ✅ Always import from module_api
import { useUserQueries, useUserNavigation } from '@/modules/users'

// Use the hooks and navigation
const { useUser } = useUserQueries()
const { navigateToUser } = useUserNavigation()
```

## 🚫 Common Frontend Anti-Patterns

```typescript
// ❌ DON'T: Fat component with everything
function UserProfileScreen() {
  // 50+ lines of HTTP logic - WRONG!
  const [user, setUser] = useState(null)
  const fetchUser = async () => {
    const response = await fetch(`/api/users/${id}`)
    const userData = await response.json()

    // Business logic in component - WRONG!
    if (userData.role === 'manager') {
      userData.canPromote = userData.yearsOfService >= 2
    }
    setUser(userData)
  }

  // 100+ lines of rendering
}

// ✅ DO: Thin component using module API
function UserProfileScreen() {
  const { user, isLoading } = useUser(userId)  // Module API
  const { navigateToEdit } = useUserNavigation()  // Module API

  if (isLoading) return <LoadingSpinner />
  return <UserDetails user={user} onEdit={() => navigateToEdit(userId)} />
}

// ❌ DON'T: Business logic in query hooks
function useUser(id: number) {
  return useQuery(['user', id], async () => {
    const user = await userApi.getUser(id)

    // Complex business logic in hook - WRONG PLACE!
    if (user.role === 'manager') {
      user.canPromote = calculatePromotionEligibility(user)
      user.teamSize = await calculateTeamSize(user.id)
    }
    return user
  })
}

// ✅ DO: Delegate business logic to internal layer
function useUser(id: number) {
  return useQuery(['user', id],
    () => userApi.getUser(id),
    {
      select: (user) => ({
        ...user,
        canPromote: UserBusinessRules.canBePromoted(user),  // Internal business logic
        displayName: UserFormatter.formatDisplayName(user)  // Internal formatter
      })
    }
  )
}
```

## 🎯 Mobile-Specific Patterns

### Platform-Aware Styling
```typescript
// Platform logic in components only
const styles = StyleSheet.create({
  card: {
    ...Platform.select({
      ios: { shadowColor: '#000', shadowOpacity: 0.1 },
      android: { elevation: 4 }
    })
  }
})
```

### Offline Business Rules
```typescript
// Client business logic handles offline scenarios
export class UserBusinessRules {
  static canPerformAction(user: User, action: string): boolean {
    if (!NetworkService.isOnline()) {
      const offlineActions = ['view_profile', 'edit_basic_info']
      return offlineActions.includes(action)
    }
    return user.permissions.includes(action)
  }
}
```

### App State Handling
```typescript
// Module API coordinates app state changes
export function useUserQueries() {
  const queryClient = useQueryClient()

  // Refetch when app becomes active
  useFocusEffect(
    useCallback(() => {
      queryClient.refetchQueries(['users'])
    }, [queryClient])
  )

  return { /* queries */ }
}
```

## 🚀 Benefits Summary

- **Screen Layer**: Pure UI rendering, easy to test and maintain
- **Module API**: Centralized state management with cross-module interface
- **HTTP Client**: Clean backend communication isolated per module
- **Internal Layer**: Reusable business logic and formatting
- **Navigation**: Module-specific routing with cross-module actions

The key is keeping **UI pure**, **state centralized**, **HTTP isolated**, **business logic in domain**, and **platform concerns in infrastructure** while handling mobile-specific requirements!