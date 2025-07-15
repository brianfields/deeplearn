# Component Types Migration Guide

> **⚠️ DEPRECATED**: This guide is for historical reference. The `ComponentRenderer` system has been replaced by `DuolingoLearningFlow.tsx` which handles component rendering directly. The generic `ComponentRenderer`, `useComponentSequence`, and `createTypedComponent` utilities have been removed as dead code.

This document provides a comprehensive guide for migrating from generic `content` props to specific TypeScript types for bite-sized learning components.

## Overview

This document outlines the new TypeScript type system for bite-sized learning components, replacing the previous generic `any` types with specific, type-safe interfaces.

## Why This Change?

### Before (Problems)
```typescript
// ❌ Old approach - no type safety
interface TopicComponent {
  component_type: ComponentType
  content: any  // Could be anything!
  metadata: Record<string, any>
}

// ❌ Inconsistent prop patterns
<DidacticSnippet content={...} onContinue={...} />
<MultipleChoice questions={...} onComplete={...} />
<PostTopicQuiz quizData={...} onComplete={...} onRetry={...} />
```

### After (Benefits)
```typescript
// ✅ New approach - full type safety
interface TypedTopicComponent<T extends ComponentType> {
  component_type: T
  content: T extends 'didactic_snippet' ? DidacticSnippetContent :
           T extends 'multiple_choice_question' ? MultipleChoiceContent :
           // ... specific types for each component
  metadata: ComponentMetadata
}

// ✅ Consistent prop patterns
<ComponentRenderer component={typedComponent} onComplete={handleComplete} />
```

## Benefits of the New System

### 1. **Type Safety**
- Eliminates `any` types
- Compile-time error checking
- IntelliSense support for all component properties

### 2. **Consistency**
- Standardized prop interfaces across all components
- Unified callback patterns (`OnComponentComplete`)
- Common base props (`BaseLearningComponentProps`)

### 3. **Maintainability**
- Centralized type definitions
- Easy to add new component types
- Clear component contracts

### 4. **Developer Experience**
- Better IDE support
- Self-documenting code
- Reduced runtime errors

### 5. **Scalability**
- Generic component renderer
- Type-safe component factories
- Easy testing of component interfaces

## New Type System Structure

### Base Types
```typescript
// Common interface for all learning components
interface BaseLearningComponentProps {
  isLoading?: boolean
  onError?: (error: string) => void
}

// Standardized completion callback
type OnComponentComplete = (results: ComponentResults) => void

// Results with type information
interface ComponentResults {
  componentType: ComponentType
  timeSpent: number
  completed: boolean
  data: any // Specific to component type
}
```

### Component-Specific Types

Each component now has dedicated types:

```typescript
// Didactic Snippet
interface DidacticSnippetContent {
  title: string
  core_concept: string
  main_content: string
  key_points: string[]
  learning_objectives: string[]
  estimated_duration: number
}

interface DidacticSnippetProps extends BaseLearningComponentProps {
  content: DidacticSnippetContent
  onContinue: () => void
}

// Multiple Choice
interface MultipleChoiceContent {
  questions: MultipleChoiceQuestion[]
}

interface MultipleChoiceProps extends BaseLearningComponentProps {
  content: MultipleChoiceContent
  onComplete: OnComponentComplete
}

// ... and so on for all component types
```

## Migration Examples

### 1. Creating Typed Components

```typescript
import { createTypedComponent } from '@/components/learning'

// ✅ Type-safe component creation
const didacticComponent = createTypedComponent('didactic_snippet', {
  title: 'Introduction to React',
  core_concept: 'Component-based architecture',
  main_content: 'React is a library...',
  key_points: ['Reusable components', 'One-way data flow'],
  learning_objectives: ['Understand components', 'Learn JSX'],
  estimated_duration: 5
}, {
  order: 1,
  estimated_duration: 5,
  difficulty: 'beginner',
  required: true
})

// TypeScript will catch errors at compile time!
const invalidComponent = createTypedComponent('didactic_snippet', {
  title: 'Test',
  // ❌ TypeScript error: missing required properties
}, {})
```

### 2. Generic Component Rendering

```typescript
import { ComponentRenderer, useComponentSequence } from '@/components/learning'

function LearningFlow({ components }: { components: TypedTopicComponent[] }) {
  const {
    currentComponent,
    progress,
    handleComponentComplete,
    isComplete
  } = useComponentSequence(components)

  if (isComplete) {
    return <div>Learning complete!</div>
  }

  return (
    <div>
      <div>Progress: {progress}%</div>
      <ComponentRenderer
        component={currentComponent}
        onComplete={handleComponentComplete}
      />
    </div>
  )
}
```

### 3. Type Guards for Runtime Safety

```typescript
import { isDidacticSnippetContent, isMultipleChoiceContent } from '@/types'

function processComponent(component: TypedTopicComponent) {
  if (component.component_type === 'didactic_snippet') {
    // TypeScript knows this is DidacticSnippetContent
    if (isDidacticSnippetContent(component.content)) {
      console.log(`Title: ${component.content.title}`)
      console.log(`Duration: ${component.content.estimated_duration}`)
    }
  }
}
```

### 4. Building Component Sequences

```typescript
const learningSequence: TypedTopicComponent[] = [
  createTypedComponent('didactic_snippet', {
    title: 'Introduction',
    core_concept: 'Basic concepts',
    main_content: 'Learn the fundamentals...',
    key_points: ['Point 1', 'Point 2'],
    learning_objectives: ['Objective 1'],
    estimated_duration: 3
  }, { order: 1, difficulty: 'beginner', required: true }),

  createTypedComponent('multiple_choice_question', {
    questions: [{
      id: '1',
      question: 'What did you learn?',
      options: [
        { id: 'a', text: 'Option A', is_correct: true },
        { id: 'b', text: 'Option B', is_correct: false }
      ]
    }]
  }, { order: 2, difficulty: 'beginner', required: true }),

  createTypedComponent('short_answer_question', {
    questions: [{
      id: '1',
      question: 'Explain the concept in your own words',
      sample_answers: ['Example answer'],
      key_concepts: ['concept1', 'concept2'],
      evaluation_criteria: ['clarity', 'completeness']
    }]
  }, { order: 3, difficulty: 'intermediate', required: false })
]
```

## Adding New Component Types

When adding a new component type:

1. **Define the content interface**:
```typescript
export interface NewComponentContent {
  // Define the structure
}
```

2. **Define the props interface**:
```typescript
export interface NewComponentProps extends BaseLearningComponentProps {
  content: NewComponentContent
  onComplete: OnComponentComplete
}
```

3. **Define the results interface**:
```typescript
export interface NewComponentResults {
  // Define the results structure
}
```

4. **Add to union types**:
```typescript
export type ComponentContent =
  | DidacticSnippetContent
  | MultipleChoiceContent
  | NewComponentContent  // Add here
  // ... other types
```

5. **Add type guard**:
```typescript
export function isNewComponentContent(content: ComponentContent): content is NewComponentContent {
  return 'uniqueProperty' in content
}
```

6. **Update the ComponentRenderer**:
```typescript
case 'new_component': {
  if (!isNewComponentContent(content)) {
    throw new Error('Invalid content for new component')
  }

  return <NewComponent content={content} onComplete={onComplete} />
}
```

## Testing with the New Types

```typescript
import { createTypedComponent, ComponentRenderer } from '@/components/learning'
import { render, fireEvent } from '@testing-library/react'

describe('Typed Components', () => {
  it('should render didactic snippet correctly', () => {
    const component = createTypedComponent('didactic_snippet', {
      title: 'Test Title',
      core_concept: 'Test Concept',
      main_content: 'Test Content',
      key_points: ['Point 1'],
      learning_objectives: ['Objective 1'],
      estimated_duration: 5
    }, {
      order: 1,
      difficulty: 'beginner',
      required: true
    })

    const handleComplete = jest.fn()

    const { getByText } = render(
      <ComponentRenderer component={component} onComplete={handleComplete} />
    )

    expect(getByText('Test Title')).toBeInTheDocument()
  })
})
```

## Best Practices

1. **Always use the typed system for new components**
2. **Prefer `ComponentRenderer` over direct component usage**
3. **Use `createTypedComponent` for creating components**
4. **Add type guards for runtime validation**
5. **Keep component interfaces minimal and focused**
6. **Use the `useComponentSequence` hook for managing flows**

## Deprecation Timeline

- ✅ **Now**: New typed system available
- 🔄 **Next Sprint**: Migrate existing usages
- ⚠️ **Sprint +2**: Mark old interfaces as deprecated
- ❌ **Sprint +4**: Remove old interfaces

The new typed system provides a solid foundation for scaling your learning component library while maintaining type safety and developer productivity.