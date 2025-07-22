# Frontend Architecture

## Overview

The frontend is organized into three clear functional areas that map directly to user workflows:

- **🏠 Dashboard** - Browse topics, view progress, main hub
- **🎨 Studio** - Create and edit learning content
- **📚 Learn** - Active learning sessions

## Directory Structure

```
web/src/
├── app/                                    # Next.js App Router
│   ├── dashboard/
│   │   └── page.tsx                        # Main dashboard - browse topics
│   ├── studio/                             # Content creation area
│   │   ├── page.tsx                        # Studio landing - topic management
│   │   └── [topicId]/
│   │       └── page.tsx                    # Edit specific topic
│   ├── learn/                              # Learning experiences
│   │   └── [topicId]/
│   │       └── page.tsx                    # Active learning session
│   ├── page.tsx                            # Root - redirects to /dashboard
│   └── layout.tsx                          # App-wide layout
├── components/
│   ├── dashboard/
│   │   └── DashboardOverview.tsx           # Main dashboard component
│   ├── studio/
│   │   ├── MaterialInputForm.tsx           # Content creation form
│   │   └── RefinedMaterialView.tsx         # Material editing interface
│   ├── learning/                           # Interactive learning components
│   │   ├── DuolingoLearningFlow.tsx        # Main learning orchestrator
│   │   ├── DidacticSnippet.tsx             # Content presentation
│   │   ├── MultipleChoice.tsx              # MCQ interactions
│   │   ├── ShortAnswer.tsx                 # Open-ended questions
│   │   ├── SocraticDialogue.tsx            # Conversational learning
│   │   ├── PostTopicQuiz.tsx               # Assessment component
│   │   └── index.ts                        # Learning component exports
│   ├── shared/                             # App-wide shared components
│   │   ├── Header.tsx                      # Navigation header
│   │   └── Layout.tsx                      # Page layout wrapper
│   └── ui/                                 # shadcn/ui components
├── hooks/
│   ├── dashboard/
│   │   └── useBiteSizedTopics.ts           # Topic management state
│   ├── learning/
│   │   └── useDuolingoLearning.ts          # Learning session state
│   └── index.ts                            # Hook exports
├── services/
│   ├── learning/
│   │   └── learning-flow.ts                # Learning session business logic
│   └── index.ts                            # Service exports
└── types/
    ├── components.ts                       # Component type definitions
    ├── api.ts                              # API type definitions
    └── index.ts                            # Type exports
```

## URL Structure

| Route | Purpose | Description |
|-------|---------|-------------|
| `/` | Root | Redirects to `/dashboard` |
| `/dashboard` | Dashboard | Browse topics, view progress, main hub |
| `/studio` | Studio Landing | Manage topics, create new content |
| `/studio/new` | Create Topic | Create new learning topic |
| `/studio/[topicId]` | Edit Topic | Edit existing topic content |
| `/learn/[topicId]` | Learning Session | Active learning experience |

## Component Organization

### Dashboard Components (`/dashboard`)
- **Purpose**: Topic browsing, progress tracking, navigation
- **Key Component**: `DashboardOverview.tsx`
- **Hook**: `useBiteSizedTopics.ts`

### Studio Components (`/studio`)
- **Purpose**: Content creation and editing
- **Key Components**: `MaterialInputForm.tsx`, `RefinedMaterialView.tsx`
- **Routes**: Studio landing, new topic creation, topic editing

### Learning Components (`/learning`)
- **Purpose**: Interactive learning experiences
- **Key Component**: `DuolingoLearningFlow.tsx` (orchestrator)
- **Interactive Components**: Multiple choice, short answer, socratic dialogue, etc.
- **Hook**: `useDuolingoLearning.ts`
- **Service**: `learning-flow.ts`

### Shared Components (`/shared`)
- **Purpose**: App-wide navigation and layout
- **Key Components**: `Header.tsx`, `Layout.tsx`

## Design Principles

### Clear Separation of Concerns
- Each area has dedicated components, hooks, and services
- Business logic is isolated in services
- React state management in hooks
- UI components focus only on presentation

### Intuitive Navigation
- URLs clearly indicate purpose: `/studio` for creation, `/learn` for learning
- Consistent navigation patterns across all areas
- Header adapts based on current context

### Scalable Architecture
- Each area can grow independently
- Services are framework-agnostic and reusable
- Hook/service pattern separates view and business logic
- Component composition over large monolithic components

### Developer Experience
- Clear file naming conventions
- Logical grouping by feature area
- Minimal import statement complexity
- Self-documenting directory structure

## Key Features

### Dashboard
- Topic overview and browsing
- Progress tracking and streaks
- Quick actions (create, edit, learn)
- Achievement display

### Studio
- Topic creation from source material
- Content refinement and editing
- Component generation and management
- Preview and publishing tools

### Learning
- Adaptive learning flow
- Multiple interaction types
- Progress persistence
- Offline capability
- Duolingo-style UX patterns

## Migration Notes

This structure replaces the previous organization which had:
- Mixed component locations
- Unclear URL patterns (`/content-creation`, `/topic`)
- Over-engineered hooks (`useLearningPaths`)
- Unused features (courses)

The new structure is simpler, more intuitive, and better supports the three core user workflows.