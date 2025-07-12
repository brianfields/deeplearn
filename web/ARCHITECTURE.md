# Frontend Architecture Documentation

## Overview

This document describes the architecture and conventions for the Learning Platform frontend, which has been organized to provide clear separation of concerns and maintainable code structure.

## Table of Contents

- [Architecture Principles](#architecture-principles)
- [Directory Structure](#directory-structure)
- [Layer Responsibilities](#layer-responsibilities)
- [Development Conventions](#development-conventions)
- [Data Flow](#data-flow)
- [Error Handling](#error-handling)
- [Performance Considerations](#performance-considerations)
- [Testing Strategy](#testing-strategy)

## Architecture Principles

### 1. Separation of Concerns
- **Presentation Logic**: Components focus solely on rendering UI
- **Business Logic**: Services handle domain operations
- **Data Access**: API layer manages server communication
- **State Management**: Hooks encapsulate stateful logic

### 2. Dependency Direction
```
Components → Hooks → Services → API → Backend
```
- Each layer only depends on the layer below it
- No circular dependencies between layers
- Clear data flow from backend to UI

### 3. Type Safety
- Comprehensive TypeScript types for all interfaces
- Strict type checking enabled
- Runtime validation for critical data

### 4. Modularity
- Small, focused modules with single responsibilities
- Clear interfaces between modules
- Easy to test and maintain

## Directory Structure

```
src/
├── api/                    # API communication layer
│   ├── client.ts          # HTTP client with retry/error handling
│   ├── websocket.ts       # WebSocket client for real-time communication
│   └── index.ts           # API exports
├── services/              # Business logic layer
│   ├── learning.ts        # Learning paths business logic
│   ├── conversation.ts    # Conversation management
│   └── index.ts           # Services exports
├── hooks/                 # React hooks for stateful logic
│   ├── useLearningPaths.ts # Learning paths state management
│   ├── useConversation.ts  # Conversation state management
│   └── index.ts           # Hooks exports
├── components/            # UI components
│   ├── ui/                # Reusable UI primitives
│   ├── LearnInterface.tsx # Feature-specific components
│   └── ...
├── types/                 # TypeScript type definitions
│   ├── index.ts           # Core domain types
│   └── api.ts             # API-specific types
├── utils/                 # Pure utility functions
│   ├── formatting.ts      # Data formatting utilities
│   ├── validation.ts      # Input validation utilities
│   ├── cn.ts              # CSS class utilities
│   └── index.ts           # Utils exports
├── app/                   # Next.js app router pages
└── lib/                   # Third-party library configurations
```

## Layer Responsibilities

### 1. API Layer (`src/api/`)

**Purpose**: Handle all communication with the backend server

**Responsibilities**:
- HTTP requests with proper error handling
- WebSocket connections for real-time features
- Request/response transformation
- Retry logic and timeout handling
- Connection state management

**Key Files**:
- `client.ts`: Main HTTP client with retry logic
- `websocket.ts`: WebSocket client for conversations
- `index.ts`: Clean exports for the entire API layer

**Usage**:
```typescript
import { apiClient, ConversationWebSocket } from '@/api'

// HTTP requests
const paths = await apiClient.getLearningPaths()

// WebSocket connections
const ws = new ConversationWebSocket(topicId)
```

### 2. Services Layer (`src/services/`)

**Purpose**: Implement business logic and domain operations

**Responsibilities**:
- Complex business operations
- Data validation and transformation
- Caching and optimization
- API call orchestration
- Domain-specific calculations

**Key Files**:
- `learning.ts`: Learning paths operations
- `conversation.ts`: Real-time conversation management
- `index.ts`: Services exports

**Usage**:
```typescript
import { learningService, conversationService } from '@/services'

// Business operations
const enhancedPath = await learningService.getLearningPath(pathId)
const conversation = await conversationService.startConversation({ pathId, topicId })
```

### 3. Hooks Layer (`src/hooks/`)

**Purpose**: Encapsulate stateful logic for React components

**Responsibilities**:
- Component state management
- Side effects (useEffect)
- Service layer integration
- Loading and error states
- Optimistic updates

**Key Files**:
- `useLearningPaths.ts`: Learning paths state management
- `useConversation.ts`: Conversation state and WebSocket management
- `index.ts`: Hooks exports

**Usage**:
```typescript
import { useLearningPaths, useConversation } from '@/hooks'

// In React components
const { learningPaths, createPath, isLoading } = useLearningPaths()
const { messages, sendMessage, isConnected } = useConversation(pathId, topicId)
```

### 4. Types Layer (`src/types/`)

**Purpose**: Define TypeScript interfaces and types

**Responsibilities**:
- Domain model definitions
- API contract types
- UI component prop types
- Utility type definitions

**Key Files**:
- `index.ts`: Core domain types (LearningPath, Topic, etc.)
- `api.ts`: API-specific types (requests, responses, errors)

**Usage**:
```typescript
import type { LearningPath, ChatMessage, ApiError } from '@/types'
```

### 5. Utils Layer (`src/utils/`)

**Purpose**: Provide pure utility functions

**Responsibilities**:
- Data formatting
- Input validation
- Helper functions
- No side effects or state

**Key Files**:
- `formatting.ts`: Date, time, number formatting
- `validation.ts`: Input validation functions
- `cn.ts`: CSS class name utilities
- `index.ts`: Utils exports

**Usage**:
```typescript
import { formatDuration, validateEmail, cn } from '@/utils'
```

### 6. Components Layer (`src/components/`)

**Purpose**: Render UI and handle user interactions

**Responsibilities**:
- User interface rendering
- Event handling
- Local component state (forms, UI state)
- Hooks integration

**Best Practices**:
- Keep components focused and small
- Use hooks for state management
- Delegate business logic to services
- Use TypeScript for prop validation

## Development Conventions

### 1. File Naming

- **Components**: PascalCase (e.g., `LearnInterface.tsx`)
- **Hooks**: camelCase starting with "use" (e.g., `useLearningPaths.ts`)
- **Services**: camelCase (e.g., `learningService.ts`)
- **Types**: camelCase (e.g., `index.ts`, `api.ts`)
- **Utils**: camelCase (e.g., `formatting.ts`)

### 2. Import Organization

```typescript
// 1. React and third-party imports
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

// 2. Type imports (using 'type' keyword)
import type { LearningPath, ChatMessage } from '@/types'

// 3. Local imports (services, hooks, utils)
import { learningService } from '@/services'
import { useLearningPaths } from '@/hooks'
import { formatDuration } from '@/utils'
```

### 3. Function Definitions

- **Pure functions**: Regular function declarations
- **React components**: Arrow functions for functional components
- **Hooks**: Arrow functions exported as named exports
- **Services**: Class methods or object methods

### 4. Error Handling

```typescript
// Services layer - transform and categorize errors
try {
  const result = await apiClient.getSomething()
  return result
} catch (error) {
  if (error instanceof ApiError) {
    throw error
  }
  throw new Error(`Failed to get something: ${error}`)
}

// Hooks layer - provide error state to components
const [error, setError] = useState<string | null>(null)

try {
  await serviceOperation()
} catch (error) {
  setError(error.message)
}

// Components layer - display errors to users
if (error) {
  return <ErrorAlert message={error} onClose={clearError} />
}
```

### 5. State Management

- **Local UI state**: `useState` in components
- **Complex state**: Custom hooks
- **Global state**: Services with caching
- **Server state**: React Query patterns in hooks

## Data Flow

### 1. Reading Data

```
Backend → API Client → Service → Hook → Component
```

1. **API Client** fetches data from backend
2. **Service** processes and caches data
3. **Hook** manages loading/error states
4. **Component** renders data

### 2. Writing Data

```
Component → Hook → Service → API Client → Backend
```

1. **Component** triggers action (button click)
2. **Hook** handles loading state
3. **Service** validates and processes data
4. **API Client** sends request to backend

### 3. Real-time Updates

```
Backend → WebSocket → Service → Hook → Component
```

1. **WebSocket** receives real-time updates
2. **Service** processes incoming messages
3. **Hook** updates component state
4. **Component** renders new data

## Error Handling Strategy

### 1. Error Categories

- **Network Errors**: Connection failures, timeouts
- **API Errors**: 4xx/5xx HTTP responses
- **Validation Errors**: Invalid user input
- **Business Logic Errors**: Domain-specific errors

### 2. Error Handling Layers

- **API Layer**: Retry logic, error transformation
- **Service Layer**: Business logic validation
- **Hook Layer**: Error state management
- **Component Layer**: User-friendly error display

### 3. Error Recovery

- **Automatic Retry**: Network errors with exponential backoff
- **User Retry**: Manual retry buttons for failed operations
- **Fallback UI**: Graceful degradation when features fail
- **Error Boundaries**: Catch and handle React errors

## Performance Considerations

### 1. API Optimization

- **Caching**: Service-level caching with TTL
- **Batching**: Combine multiple requests when possible
- **Lazy Loading**: Load data when needed
- **Pagination**: Implement for large datasets

### 2. Component Optimization

- **React.memo**: Prevent unnecessary re-renders
- **useMemo/useCallback**: Memoize expensive operations
- **Code Splitting**: Lazy load components
- **Virtualization**: For long lists

### 3. Bundle Optimization

- **Tree Shaking**: Remove unused code
- **Dynamic Imports**: Load features on demand
- **Asset Optimization**: Compress images and assets

## Testing Strategy

### 1. Unit Testing

- **Utils**: Test all utility functions
- **Services**: Test business logic
- **Hooks**: Test state management
- **Components**: Test rendering and interactions

### 2. Integration Testing

- **API Layer**: Test with mock backend
- **Service + Hook**: Test data flow
- **Component + Hook**: Test user interactions

### 3. E2E Testing

- **Critical Paths**: User registration, learning flows
- **Real-time Features**: WebSocket functionality
- **Error Scenarios**: Network failures, validation errors

## Getting Started

### 1. Adding a New Feature

1. **Define Types** in `src/types/`
2. **Create API Methods** in `src/api/`
3. **Implement Service Logic** in `src/services/`
4. **Create Hooks** in `src/hooks/`
5. **Build Components** in `src/components/`

### 2. Modifying Existing Features

1. **Update Types** if data structure changes
2. **Modify Service Logic** for business rule changes
3. **Update Hooks** for new state requirements
4. **Adjust Components** for UI changes

### 3. Adding Utilities

1. **Pure Functions** go in `src/utils/`
2. **Export** from appropriate module
3. **Add to Index** for easy importing
4. **Write Tests** for all utilities

## Best Practices Summary

1. **Keep layers focused** - each layer has a single responsibility
2. **Use TypeScript** - comprehensive type definitions
3. **Handle errors gracefully** - at every layer
4. **Cache appropriately** - in services layer
5. **Test thoroughly** - unit, integration, and E2E
6. **Document decisions** - update this documentation
7. **Follow conventions** - consistent naming and structure
8. **Review regularly** - architecture evolves with requirements

---

This architecture provides a solid foundation for building maintainable, scalable frontend applications. Follow these conventions to ensure consistency and quality across the codebase.