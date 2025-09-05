# Learning Session Module (Frontend)

## Purpose

This frontend module provides the user interface for active learning experiences and session management. It handles the real-time learning flow, component rendering, and session interaction without managing historical progress or topic discovery.

## Domain Responsibility

**"Active learning session user interface and real-time learning experience"**

The Learning Session frontend module owns all UI aspects of active learning:

- Learning flow orchestration and component rendering
- Real-time session progress tracking and display
- Interactive component handling (MCQ, didactic snippets, etc.)
- Session state management and persistence
- Immediate feedback and results display
- Session navigation and flow control

## Architecture

### Module API (Public Interface)

```typescript
// module_api/index.ts
export { useLearningSession } from './queries';
export { useLearningSessionStore } from './store';
export { useLearningSessionNavigation } from './navigation';
export type { LearningSession, SessionProgress, SessionResults } from './types';

// module_api/queries.ts
export function useLearningSession() {
  return {
    useStartSession: () =>
      useMutation({
        mutationFn: ({ topicId, userId }: StartSessionRequest) =>
          startSessionUseCase(topicId, userId),
        onSuccess: session => {
          SessionStore.setActiveSession(session);
          AnalyticsAdapter.track('session_started', {
            topicId: session.topicId,
          });
        },
      }),

    useSessionProgress: (sessionId: string) =>
      useQuery({
        queryKey: ['session', sessionId, 'progress'],
        queryFn: () => getSessionProgressUseCase(sessionId),
        refetchInterval: 5000, // Real-time updates
        enabled: !!sessionId,
      }),

    useSubmitInteraction: () =>
      useMutation({
        mutationFn: ({ sessionId, interaction }: SubmitInteractionRequest) =>
          submitInteractionUseCase(sessionId, interaction),
        onSuccess: progress => {
          SessionStore.updateProgress(progress);
        },
      }),

    useCompleteSession: () =>
      useMutation({
        mutationFn: (sessionId: string) => completeSessionUseCase(sessionId),
        onSuccess: results => {
          SessionStore.clearActiveSession();
          // Results will be consumed by Learning Analytics module
        },
      }),
  };
}

// module_api/navigation.ts
export function useLearningSessionNavigation() {
  const navigation = useNavigation();

  return {
    navigateToLearningFlow: (topic: Topic) =>
      navigation.navigate('LearningSession', {
        screen: 'LearningFlow',
        params: { topic },
      }),

    navigateToResults: (results: SessionResults) =>
      navigation.navigate('LearningSession', {
        screen: 'Results',
        params: { results },
      }),

    navigateBack: () => navigation.goBack(),
  };
}
```

### Screens (UI Layer)

```typescript
// screens/LearningFlowScreen.tsx
export function LearningFlowScreen({ route }: Props) {
  const { topic } = route.params
  const { useStartSession } = useLearningSession()
  const { navigateToResults, navigateBack } = useLearningSessionNavigation()

  const startSessionMutation = useStartSession()

  useEffect(() => {
    startSessionMutation.mutate({
      topicId: topic.id,
      userId: 'current-user' // TODO: Get from auth
    })
  }, [topic.id])

  const handleSessionComplete = (results: SessionResults) => {
    navigateToResults(results)
  }

  const handleBack = () => {
    // Show confirmation dialog for active session
    Alert.alert(
      'Exit Learning?',
      'Your progress will be saved.',
      [
        { text: 'Continue Learning', style: 'cancel' },
        { text: 'Exit', onPress: navigateBack }
      ]
    )
  }

  if (startSessionMutation.isLoading) {
    return <LoadingScreen message="Starting your learning session..." />
  }

  if (startSessionMutation.error) {
    return <ErrorScreen error={startSessionMutation.error} onRetry={() => startSessionMutation.mutate()} />
  }

  return (
    <SafeAreaView style={styles.container}>
      <LearningFlow
        session={startSessionMutation.data}
        topic={topic}
        onComplete={handleSessionComplete}
        onBack={handleBack}
      />
    </SafeAreaView>
  )
}

// screens/ResultsScreen.tsx
export function ResultsScreen({ route }: Props) {
  const { results } = route.params
  const { navigateBack } = useLearningSessionNavigation()
  const { navigateToTopicCatalog } = useTopicCatalogNavigation()

  return (
    <ScrollView style={styles.container}>
      <SessionResultsHeader results={results} />
      <ScoreDisplay score={results.score} />
      <TimeSpentDisplay duration={results.total_duration} />
      <InteractionSummary interactions={results.interactions} />

      <View style={styles.actions}>
        <Button
          title="Continue Learning"
          onPress={navigateToTopicCatalog}
          style={styles.primaryButton}
        />
        <Button
          title="Review Session"
          onPress={() => {/* Navigate to session review */}}
          style={styles.secondaryButton}
        />
      </View>
    </ScrollView>
  )
}
```

### Components (Learning Components)

```typescript
// components/LearningFlow.tsx
interface LearningFlowProps {
  session: LearningSession
  topic: Topic
  onComplete: (results: SessionResults) => void
  onBack: () => void
}

export function LearningFlow({ session, topic, onComplete, onBack }: LearningFlowProps) {
  const { useSessionProgress, useSubmitInteraction, useCompleteSession } = useLearningSession()

  const { data: progress } = useSessionProgress(session.id)
  const submitInteractionMutation = useSubmitInteraction()
  const completeSessionMutation = useCompleteSession()

  const currentComponent = progress?.current_component
  const progressPercentage = ProgressRules.calculatePercentage(progress)

  const handleInteraction = async (interaction: InteractionResult) => {
    const updatedProgress = await submitInteractionMutation.mutateAsync({
      sessionId: session.id,
      interaction
    })

    // Check if session is complete
    if (SessionCompletionRules.isComplete(updatedProgress)) {
      const results = await completeSessionMutation.mutateAsync(session.id)
      onComplete(results)
    }
  }

  return (
    <View style={styles.container}>
      <SessionHeader
        topic={topic}
        progress={progressPercentage}
        onBack={onBack}
      />

      <ComponentRenderer
        component={currentComponent}
        onInteraction={handleInteraction}
        isLoading={submitInteractionMutation.isLoading}
      />

      <SessionFooter
        currentStep={progress?.current_step || 0}
        totalSteps={progress?.total_steps || 0}
      />
    </View>
  )
}

// components/ComponentRenderer.tsx
interface ComponentRendererProps {
  component: LearningComponent
  onInteraction: (interaction: InteractionResult) => void
  isLoading: boolean
}

export function ComponentRenderer({ component, onInteraction, isLoading }: ComponentRendererProps) {
  if (!component) {
    return <LoadingSpinner />
  }

  switch (component.component_type) {
    case 'didactic_snippet':
      return (
        <DidacticSnippet
          content={component.content}
          onContinue={() => onInteraction({
            componentId: component.id,
            type: 'continue',
            timeSpent: Date.now() - startTime
          })}
          isLoading={isLoading}
        />
      )

    case 'mcq':
      return (
        <MultipleChoice
          question={component.content}
          onAnswer={(answer) => onInteraction({
            componentId: component.id,
            type: 'mcq_answer',
            answer: answer,
            timeSpent: Date.now() - startTime
          })}
          isLoading={isLoading}
        />
      )

    case 'socratic_dialogue':
      return (
        <SocraticDialogue
          dialogue={component.content}
          onComplete={(responses) => onInteraction({
            componentId: component.id,
            type: 'dialogue_complete',
            responses: responses,
            timeSpent: Date.now() - startTime
          })}
          isLoading={isLoading}
        />
      )

    default:
      return <UnsupportedComponent type={component.component_type} />
  }
}

// components/MultipleChoice.tsx
interface MultipleChoiceProps {
  question: MCQContent
  onAnswer: (answer: string) => void
  isLoading: boolean
}

export function MultipleChoice({ question, onAnswer, isLoading }: MultipleChoiceProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)

  const handleAnswerSelect = (answer: string) => {
    setSelectedAnswer(answer)
  }

  const handleSubmit = () => {
    if (selectedAnswer) {
      onAnswer(selectedAnswer)
      setShowFeedback(true)

      // Auto-advance after showing feedback
      setTimeout(() => {
        setShowFeedback(false)
        setSelectedAnswer(null)
      }, 3000)
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.question}>{question.question}</Text>

      <View style={styles.choices}>
        {Object.entries(question.choices).map(([key, choice]) => (
          <ChoiceButton
            key={key}
            choice={choice}
            isSelected={selectedAnswer === key}
            isCorrect={showFeedback && key === question.correct_answer}
            isIncorrect={showFeedback && selectedAnswer === key && key !== question.correct_answer}
            onPress={() => handleAnswerSelect(key)}
            disabled={showFeedback || isLoading}
          />
        ))}
      </View>

      {showFeedback && (
        <FeedbackDisplay
          isCorrect={selectedAnswer === question.correct_answer}
          justification={question.justifications[selectedAnswer!]}
        />
      )}

      <Button
        title="Submit Answer"
        onPress={handleSubmit}
        disabled={!selectedAnswer || showFeedback || isLoading}
        loading={isLoading}
      />
    </View>
  )
}
```

### Application Layer (Use Cases)

```typescript
// application/startSession.usecase.ts
export async function startSessionUseCase(
  topicId: string,
  userId: string
): Promise<LearningSession> {
  try {
    // Check for existing active session
    const existingSession = await SessionStorageAdapter.getActiveSession(
      userId,
      topicId
    );
    if (existingSession && SessionRules.canResume(existingSession)) {
      AnalyticsAdapter.track('session_resumed', {
        sessionId: existingSession.id,
      });
      return existingSession;
    }

    // Start new session
    const session = await learningSessionApi.startSession({ topicId, userId });

    // Cache session for offline access
    await SessionStorageAdapter.cacheSession(session);

    // Initialize session state
    SessionProgressAdapter.initializeProgress(session);

    AnalyticsAdapter.track('session_started', {
      sessionId: session.id,
      topicId: topicId,
    });

    return session;
  } catch (error) {
    // Handle offline scenario
    if (NetworkAdapter.isOffline()) {
      const cachedSession = await SessionStorageAdapter.createOfflineSession(
        topicId,
        userId
      );
      return cachedSession;
    }
    throw error;
  }
}

// application/submitInteraction.usecase.ts
export async function submitInteractionUseCase(
  sessionId: string,
  interaction: InteractionResult
): Promise<SessionProgress> {
  try {
    // Validate interaction
    if (!InteractionRules.isValid(interaction)) {
      throw new InvalidInteractionError('Invalid interaction data');
    }

    // Submit to backend
    const progress = await learningSessionApi.submitInteraction(
      sessionId,
      interaction
    );

    // Update local progress
    await SessionProgressAdapter.updateProgress(sessionId, progress);

    // Calculate and store metrics
    const metrics = SessionMetricsRules.calculateMetrics(interaction, progress);
    await SessionMetricsAdapter.storeMetrics(sessionId, metrics);

    // Provide immediate feedback
    FeedbackAdapter.showInteractionFeedback(interaction, progress);

    return progress;
  } catch (error) {
    // Handle offline interaction
    if (NetworkAdapter.isOffline()) {
      const offlineProgress =
        await SessionProgressAdapter.handleOfflineInteraction(
          sessionId,
          interaction
        );
      return offlineProgress;
    }
    throw error;
  }
}
```

### Domain Layer (Business Rules)

```typescript
// domain/business-rules/progress-rules.ts
export class ProgressRules {
  static calculatePercentage(progress: SessionProgress): number {
    if (!progress || progress.total_steps === 0) return 0;
    return Math.round((progress.current_step / progress.total_steps) * 100);
  }

  static shouldAdvanceStep(
    interaction: InteractionResult,
    component: LearningComponent
  ): boolean {
    switch (component.component_type) {
      case 'didactic_snippet':
        return interaction.type === 'continue';

      case 'mcq':
        return interaction.type === 'mcq_answer' && !!interaction.answer;

      case 'socratic_dialogue':
        return (
          interaction.type === 'dialogue_complete' &&
          interaction.responses?.length > 0
        );

      default:
        return false;
    }
  }

  static calculateSessionScore(interactions: InteractionResult[]): number {
    const scoredInteractions = interactions.filter(
      i => i.type === 'mcq_answer'
    );
    if (scoredInteractions.length === 0) return 0;

    const correctAnswers = scoredInteractions.filter(i => i.isCorrect).length;
    return Math.round((correctAnswers / scoredInteractions.length) * 100);
  }
}

// domain/business-rules/session-completion-rules.ts
export class SessionCompletionRules {
  static isComplete(progress: SessionProgress): boolean {
    return progress.current_step >= progress.total_steps;
  }

  static canComplete(
    session: LearningSession,
    interactions: InteractionResult[]
  ): boolean {
    // All components must have at least one interaction
    const componentIds = session.components.map(c => c.id);
    const interactedComponents = new Set(interactions.map(i => i.componentId));

    return componentIds.every(id => interactedComponents.has(id));
  }

  static calculateMasteryAchieved(
    score: number,
    timeSpent: number,
    targetTime: number
  ): boolean {
    const scoreThreshold = 0.8; // 80% correct
    const timeEfficiency = targetTime / timeSpent; // Should be <= 1.5 (within 150% of target)

    return score >= scoreThreshold && timeEfficiency >= 0.67;
  }
}
```

### Navigation (Module Stack)

```typescript
// navigation/LearningSessionStack.tsx
const Stack = createNativeStackNavigator<LearningSessionStackParamList>()

export function LearningSessionStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen
        name="LearningFlow"
        component={LearningFlowScreen}
      />
      <Stack.Screen
        name="Results"
        component={ResultsScreen}
        options={{
          gestureEnabled: false, // Prevent swipe back from results
          headerShown: true,
          title: 'Session Complete'
        }}
      />
    </Stack.Navigator>
  )
}

// navigation/types.ts
export type LearningSessionStackParamList = {
  LearningFlow: { topic: Topic }
  Results: { results: SessionResults }
}
```

## Cross-Module Communication

### Provides to Other Modules

- **Learning Analytics Module**: Session results for progress tracking

### Dependencies

- **Topic Catalog Module**: Topic selection and navigation
- **Learning Analytics Module**: Historical progress context
- **Infrastructure Module**: HTTP client, storage, analytics

### Communication Examples

```typescript
// Receive topic from Topic Catalog module
const { navigateToLearningSession } = useLearningSessionNavigation();
// Topic Catalog calls: navigateToLearningSession(selectedTopic)

// Provide results to Learning Analytics module
const sessionResults = await completeSessionUseCase(sessionId);
// Analytics module will consume these results automatically
```

## Testing Strategy

### Screen Tests (UI Behavior)

```typescript
// tests/screens/LearningFlowScreen.test.tsx
const mockTopic = { id: '1', title: 'Test Topic', components: [] }
const mockSession = { id: 'session-1', topicId: '1', userId: 'user-1' }

jest.mock('../../module_api', () => ({
  useLearningSession: () => ({
    useStartSession: () => ({
      mutate: jest.fn(),
      data: mockSession,
      isLoading: false
    })
  })
}))

describe('LearningFlowScreen', () => {
  it('starts session on mount', () => {
    const mockStartSession = jest.fn()
    jest.mocked(useLearningSession).mockReturnValue({
      useStartSession: () => ({ mutate: mockStartSession, isLoading: false })
    })

    render(<LearningFlowScreen route={{ params: { topic: mockTopic } }} />)

    expect(mockStartSession).toHaveBeenCalledWith({
      topicId: mockTopic.id,
      userId: 'current-user'
    })
  })
})
```

### Component Tests (Learning Components)

```typescript
// tests/components/MultipleChoice.test.tsx
const mockQuestion = {
  question: 'What is 2+2?',
  choices: { A: '3', B: '4', C: '5' },
  correct_answer: 'B',
  justifications: { B: 'Correct! 2+2=4' }
}

describe('MultipleChoice', () => {
  it('allows answer selection and submission', () => {
    const mockOnAnswer = jest.fn()

    render(<MultipleChoice question={mockQuestion} onAnswer={mockOnAnswer} />)

    fireEvent.press(screen.getByText('4'))
    fireEvent.press(screen.getByText('Submit Answer'))

    expect(mockOnAnswer).toHaveBeenCalledWith('B')
  })

  it('shows feedback after answer submission', async () => {
    render(<MultipleChoice question={mockQuestion} onAnswer={jest.fn()} />)

    fireEvent.press(screen.getByText('4'))
    fireEvent.press(screen.getByText('Submit Answer'))

    await waitFor(() => {
      expect(screen.getByText('Correct! 2+2=4')).toBeTruthy()
    })
  })
})
```

### Domain Tests (Business Logic)

```typescript
// tests/domain/progress-rules.test.ts
describe('ProgressRules', () => {
  it('calculates progress percentage correctly', () => {
    const progress = { current_step: 3, total_steps: 10 };

    const percentage = ProgressRules.calculatePercentage(progress);

    expect(percentage).toBe(30);
  });

  it('determines step advancement for MCQ', () => {
    const component = { component_type: 'mcq' };
    const interaction = { type: 'mcq_answer', answer: 'A' };

    const shouldAdvance = ProgressRules.shouldAdvanceStep(
      interaction,
      component
    );

    expect(shouldAdvance).toBe(true);
  });
});
```

## Real-Time Features

### Session State Synchronization

- **Auto-save**: Session state saved after each interaction
- **Real-time Updates**: Progress updates reflected immediately
- **Offline Support**: Continue learning without network connection

### Performance Optimizations

- **Component Preloading**: Preload next components for smooth transitions
- **Interaction Debouncing**: Prevent rapid-fire interactions
- **Memory Management**: Clean up resources when session ends

## Anti-Patterns to Avoid

❌ **Historical progress tracking** (belongs in Analytics module)
❌ **Topic browsing/selection** (belongs in Catalog module)
❌ **Business logic in screen components**
❌ **Direct API calls from components**
❌ **Cross-session analytics** (single session focus only)

## Module Evolution

This module can be extended with:

- **Adaptive Learning**: Adjust difficulty based on performance
- **Collaborative Sessions**: Multi-user learning sessions
- **Advanced Components**: New learning component types
- **Session Recording**: Record sessions for review
- **Accessibility**: Enhanced accessibility features

The modular architecture ensures these features can be added without affecting topic discovery or analytics functionality.
