# User Module Implementation Spec

## User Story

**As a learner**, I want to register with email/password and have my own learning space where I can:
- See my personal units (that I created) and global units (shared by others) in visually separated sections
- Create new units and choose whether to make them global (shared) or keep them personal
- Convert my existing personal units to global units via a toggle on the unit detail screen
- Continue my learning progress with all my sessions properly tracked to my user account

**As an admin user**, I want to:
- Access the admin dashboard to manage users (view, edit user information)
- See which users are associated with units, learning sessions, and LLM requests
- Have visibility into the overall system usage and content ownership

**As a content creator (regular user)**, I want to:
- Create learning units that belong to me by default
- Choose to share my units globally when I create them
- Toggle the global sharing of my existing units from the unit detail screen

## Requirements Summary

### What to Build
- Complete user authentication system with email/password registration and login
- User ownership model for units with global sharing capability
- User-aware content display with visual separation of personal vs global units
- Admin interface for user management and content oversight
- User context tracking across all user activities (units, learning sessions, LLM requests)

### Constraints
- Simple email/password authentication (no external providers initially)
- Database will be reset - no backward compatibility needed
- Only admin users can access admin dashboard
- All existing models with user_id fields should be properly utilized

### Acceptance Criteria
- [ ] Users can register with email/password and login
- [ ] Personal units are visually separated from global units in mobile interface
- [ ] Unit creation includes optional global sharing, unit detail allows toggling
- [ ] All user activities are tracked and visible in admin interface
- [ ] Database includes realistic seed data with mixed user/global content
- [ ] Admin users can manage other users and see content associations

## Cross-Stack Module Mapping

### Backend Implementation

#### New Module: `modules/user/`
- **models.py** - UserModel with id, email, password_hash, name, role, is_active fields
- **repo.py** - User database operations: by_id, by_email, create, update, authentication queries
- **service.py** - User registration, login/logout, profile management, password hashing
- **public.py** - UserProvider protocol exposing user lookup and authentication methods
- **routes.py** - POST /register, POST /login, GET /profile, PUT /profile endpoints
- **test_user_unit.py** - Unit tests for authentication and user management logic

#### Modified Modules:

**`modules/content/`**
- **models.py** - Add user_id (optional) and is_global (boolean, default False) to UnitModel
- **service.py** - Update UnitCreate/UnitRead DTOs, add user-aware CRUD methods, sharing logic
- **repo.py** - Add queries for user units, global units, unit ownership checks
- **public.py** - Update ContentProvider with user-aware unit operations
- **routes.py** - Add user context to unit operations, sharing endpoints

**`modules/admin/`**
- **models.py** - Add UserSummary, UserDetail, UserListResponse DTOs
- **service.py** - Add user management methods, enhance existing methods with user associations
- **routes.py** - Add GET /users, GET /users/{id}, PUT /users/{id} endpoints

**`modules/catalog/`**
- **service.py** - Update unit browsing to separate user-specific and global content
- **public.py** - Add user-aware catalog browsing methods

**`modules/llm_services/`**
- **service.py** - Ensure user_id is captured when making LLM requests
- **routes.py** - Pass authenticated user context to LLM operations

**`modules/learning_session/`**
- **service.py** - Ensure user sessions are properly associated with authenticated users
- **routes.py** - Pass user context to all session operations

### Frontend Implementation

#### Modified Module: `mobile/modules/catalog/`
- **models.ts** - Add user-related fields to Unit/UnitDetail, user ownership indicators
- **service.ts** - Add methods for user units vs global units, sharing operations  
- **repo.ts** - Add user-aware unit endpoints, sharing toggle endpoints
- **queries.ts** - Add useUserUnits, useGlobalUnits, useToggleUnitSharing hooks
- **screens/UnitListScreen.tsx** - Visual separation with "My Units" and "Global Units" sections
- **screens/UnitDetailScreen.tsx** - Add sharing toggle for unit owners
- **screens/CreateUnitScreen.tsx** - Add "Share globally" checkbox option

#### New Module: `mobile/modules/user/`
- **models.ts** - User, LoginRequest, RegisterRequest DTOs
- **service.ts** - User authentication and profile management service
- **repo.ts** - User API calls (auth, profile)
- **public.ts** - UserProvider for cross-module access
- **queries.ts** - useLogin, useRegister, useLogout, useProfile hooks
- **screens/LoginScreen.tsx** - Email/password login form
- **screens/RegisterScreen.tsx** - User registration form
- **test_user_unit.ts** - User module unit tests

### Admin Interface Implementation

#### New Pages:
- **admin/app/users/page.tsx** - Users list with search and filtering
- **admin/app/users/[id]/page.tsx** - User detail and edit form

#### Modified Pages:
- **admin/app/units/page.tsx** - Show unit owners and global status
- **admin/app/llm-requests/page.tsx** - Show associated users
- **Enhanced existing pages** - Add user association information throughout

## Implementation Checklist

### Backend Tasks

#### User Module Creation
- [x] Create `backend/modules/user/models.py` with UserModel
- [x] Create `backend/modules/user/repo.py` with user database operations
- [x] Create `backend/modules/user/service.py` with authentication and user management
- [x] Create `backend/modules/user/public.py` with UserProvider protocol
- [x] Create `backend/modules/user/routes.py` with registration and login endpoints
- [x] Create `backend/modules/user/test_user_unit.py` with comprehensive unit tests

#### Content Module Updates
- [x] Update `backend/modules/content/models.py` to add user_id and is_global to UnitModel
- [x] Update `backend/modules/content/repo.py` with user-aware unit queries
- [x] Update `backend/modules/content/service.py` with user ownership and sharing logic
- [x] Update `backend/modules/content/public.py` to expose user-aware operations
- [x] Update `backend/modules/content/routes.py` with user context and sharing endpoints

#### Admin Module Updates
- [ ] Update `backend/modules/admin/models.py` with user management DTOs
- [ ] Update `backend/modules/admin/service.py` with user management methods and user associations
- [ ] Update `backend/modules/admin/routes.py` with user management endpoints

#### Catalog Module Updates
- [ ] Update `backend/modules/catalog/service.py` to handle user-specific vs global content
- [ ] Update `backend/modules/catalog/public.py` with user-aware browsing methods

#### LLM Services Module Updates
- [ ] Update `backend/modules/llm_services/service.py` to capture user context in requests
- [ ] Update `backend/modules/llm_services/routes.py` to pass user context

#### Learning Session Module Updates  
- [ ] Update `backend/modules/learning_session/service.py` to ensure user association
- [ ] Update `backend/modules/learning_session/routes.py` to pass user context

#### Database and Infrastructure
- [ ] Generate Alembic migration for UserModel creation
- [ ] Generate Alembic migration for UnitModel user_id and is_global fields
- [ ] Run database migrations
- [ ] Add user router to `backend/server.py`

### Frontend Tasks

#### User Module Creation
- [ ] Create `mobile/modules/user/models.ts` with user and auth DTOs
- [ ] Create `mobile/modules/user/repo.ts` with user API calls (auth and profile)
- [ ] Create `mobile/modules/user/service.ts` with user business logic
- [ ] Create `mobile/modules/user/public.ts` with UserProvider
- [ ] Create `mobile/modules/user/queries.ts` with user hooks (auth and profile)
- [ ] Create `mobile/modules/user/screens/LoginScreen.tsx` with login form
- [ ] Create `mobile/modules/user/screens/RegisterScreen.tsx` with registration form
- [ ] Create `mobile/modules/user/test_user_unit.ts` with user module tests

#### Catalog Module Updates
- [ ] Update `mobile/modules/catalog/models.ts` with user ownership fields
- [ ] Update `mobile/modules/catalog/service.ts` with user-aware unit operations
- [ ] Update `mobile/modules/catalog/repo.ts` with user-specific endpoints
- [ ] Update `mobile/modules/catalog/queries.ts` with user and global unit hooks
- [ ] Update `mobile/modules/catalog/screens/UnitListScreen.tsx` with visual separation
- [ ] Update `mobile/modules/catalog/screens/UnitDetailScreen.tsx` with sharing toggle
- [ ] Update `mobile/modules/catalog/screens/CreateUnitScreen.tsx` with sharing option

### Admin Interface Tasks
- [ ] Create `admin/app/users/page.tsx` with users list and management
- [ ] Create `admin/app/users/[id]/page.tsx` with user detail and edit
- [ ] Update `admin/app/units/page.tsx` to show user ownership
- [ ] Update `admin/app/llm-requests/page.tsx` to show user associations
- [ ] Update other admin pages to include user information where relevant

### Data and Seed Tasks
- [ ] Update `backend/scripts/create_seed_data.py` to create sample users
- [ ] Update seed data to create mix of personal and global units
- [ ] Update seed data to associate learning sessions with users
- [ ] Update seed data to associate LLM requests with users

### Testing and Validation Tasks
- [ ] Ensure lint passes, i.e. ./format_code.sh runs clean
- [ ] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py and (in mobile) npm run test both run clean
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/users/trace.md
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code

## Notes

- Database reset means no backward compatibility concerns - can start fresh
- Existing user_id fields in LearningSessionModel, UnitSessionModel, and LLMRequestModel should be properly utilized
- Password hashing should use bcrypt or similar secure method
- Session management can be simple (database sessions or JWT)
- Visual separation in mobile app can be achieved with section headers or tabs
- Admin access control should be role-based using the user's role field
- Global unit sharing should be toggleable by unit owners only
- Seed data should include both admin and regular users for testing