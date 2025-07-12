# Proactive Learning App - Detailed Specification

## Overview
A ChatGPT-style learning app that proactively teaches professional skills through structured lessons, tracks progress, employs spaced repetition, and adapts to individual learning needs.

## Core Features

### 1. Proactive Teaching System
- **Lesson Presentation**: AI presents structured lessons rather than waiting for user questions
- **Interactive Questioning**: AI asks comprehension and application questions to assess understanding
- **Goal-Driven Learning**: Each session works toward specific learning objectives

### 2. Progress Tracking
- **Completion Marking**: Topics marked as learned with visual indicators
- **Progress Visualization**: Dashboard showing learning journey and achievements
- **Competency Mapping**: Track mastery levels across different concepts

### 3. Spaced Repetition Engine (SM-2)
- **Decay Modeling**: Progress degrades over time using forgetting curve principles
- **Review Scheduling**: Automatic scheduling of review sessions based on retention intervals
- **Adaptive Timing**: Review frequency adjusts based on individual performance

### 4. Adaptive Scaffolding
- **Dynamic Syllabus**: Course structure adjusts based on student performance and interests
- **Prerequisite Management**: Ensures foundational concepts before advanced topics
- **Personalized Pacing**: Adapts difficulty and speed to individual learning patterns

## Technical Architecture

### Stack
- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (React)
- **Database**: PostgreSQL
- **Authentication**: JWT-based user accounts

## Requirements Summary

### Learning Content
- **Subject**: Professional skills (text-based interface initially)
- **Content Generation**: AI-generated on-demand with ChatGPT-style formatting
- **Granularity**: 15-minute lessons per topic
- **Scope**: Variable syllabus size, max 20 topics

### User Experience
- **Session Length**: 15 minutes
- **Pause/Resume**: Supported
- **Platform**: Web app (mobile-responsive)
- **Offline**: Not required
- **Users**: Individual adult learners

### Assessment
- **Quiz Types**: Multiple choice, short answer, scenario critique
- **Mastery Threshold**: 90%
- **Multiple Attempts**: Allowed with review sessions between attempts
- **Progress States**: Not Started, In Progress, Partial (70-89%), Mastery (90%+)

### Spaced Repetition
- **Algorithm**: SM-2
- **Review Triggers**: Time-based and performance-based
- **Retention Goal**: Months
- **Force Review**: When mastery drops 30%

### Scaffolding
- **Triggers**: Consecutive failures, time exceeded, user request
- **Adjustments**: Add prerequisites, break down topics, adjust difficulty
- **Communication**: Syllabus update notifications with revert option

## Core User Flows

### 1. Topic Selection & Syllabus Generation
1. User enters broad topic (e.g., "Product Management")
2. AI generates initial syllabus with 15-25 topics
3. Collaborative refinement through chat interface
4. User confirms final syllabus (max 20 topics)
5. System locks syllabus and begins tracking

### 2. Learning Session (15 minutes)
1. **Review Check** (2 min): Check for degraded progress requiring review
2. **Lesson Content** (8 min): AI-generated exposition with interactive elements
3. **Comprehension Check** (5 min): Short quiz or discussion prompts

### 3. Assessment Flow
1. Complete lesson content
2. Take quiz (90% threshold for mastery)
3. If failed, require review session before retry
4. AI generates new questions for each attempt
5. Update progress and schedule next review

## User Interface Specification

### Main Navigation
- **Dashboard**: Current progress, next lesson, review alerts
- **Active Path**: Current learning path with progress indicators
- **Syllabus View**: Full topic tree with jump navigation
- **Multiple Paths**: Duolingo-style path selection (latest as default)

### Key Screens

**1. Topic Selection**
- Text input for topic description
- AI-generated syllabus preview
- Collaborative editing interface
- Confirmation/lock button

**2. Lesson Interface**
- ChatGPT-style conversation flow
- Rich text formatting (markdown support)
- Progress bar for session
- Pause/resume functionality

**3. Progress Dashboard**
- Visual progress indicators per topic
- Mastery level badges
- Review due notifications
- Time spent tracking

**4. Syllabus Management**
- Tree view of all topics
- Prerequisite relationship visualization
- Jump-to-topic navigation
- Syllabus update notifications with revert option

## Core Algorithms

### 1. Syllabus Generation
```python
def generate_syllabus(topic: str, user_level: str) -> List[Topic]:
    # AI prompt engineering for topic breakdown
    # Ensure 15-minute lesson sizing
    # Build prerequisite relationships
    # Limit to 20 topics max
```

### 2. Adaptive Difficulty
```python
def adjust_difficulty(user_performance: Dict, topic: Topic) -> Topic:
    # Monitor lesson completion time
    # Track quiz performance trends
    # Adjust content complexity
    # Modify assessment difficulty
```

### 3. SM-2 Implementation
```python
def calculate_next_review(quality: int, repetitions: int, 
                         easiness_factor: float) -> Tuple[int, float]:
    # Standard SM-2 algorithm
    # Return (interval_days, new_easiness_factor)
```

## Success Metrics
- **Engagement**: Session completion rate, time spent learning
- **Retention**: Spaced repetition quiz performance over time
- **Progress**: Topics mastered, learning path completion
- **Satisfaction**: User ratings, continued usage

## Implementation Phases
1. **Phase 1**: Basic syllabus generation and lesson delivery
2. **Phase 2**: Assessment engine and progress tracking
3. **Phase 3**: Spaced repetition system
4. **Phase 4**: Adaptive scaffolding and advanced features