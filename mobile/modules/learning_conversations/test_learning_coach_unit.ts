import { LearningCoachRepo } from './repo';
import { LearningCoachService } from './service';
import type { TeachingAssistantSessionState } from './models';

const mockRequest = jest.fn();

jest.mock('../infrastructure/public', () => ({
  infrastructureProvider: jest.fn(() => ({
    request: mockRequest,
  })),
}));

describe('LearningCoachRepo', () => {
  beforeEach(() => {
    mockRequest.mockReset();
  });

  it('converts API payload to session DTO', async () => {
    mockRequest.mockResolvedValue({
      conversation_id: 'abc-123',
      metadata: { topic: 'algebra' },
      messages: [
        {
          id: '1',
          role: 'assistant',
          content: 'Hello! Ready to learn?',
          created_at: '2024-01-01T00:00:00Z',
          metadata: {},
        },
      ],
      learning_objectives: [
        {
          id: 'lo-1',
          title: 'Objective 1',
          description: 'Objective 1 description',
        },
      ],
      proposed_brief: {
        title: 'Algebra Foundations',
        description: 'Master key concepts',
        objectives: ['Understand variables'],
        notes: 'Focus on basics',
        level: 'Beginner',
      },
      accepted_brief: null,
      resources: [
        {
          id: 'res-1',
          resource_type: 'file_upload',
          filename: 'algebra-notes.pdf',
          source_url: null,
          file_size: 1024,
          created_at: '2024-01-02T00:00:00Z',
          preview_text: 'These are algebra notes.',
        },
      ],
      uncovered_learning_objective_ids: ['lo-2', 123 as any, null as any],
    });

    const repo = new LearningCoachRepo();
    const state = await repo.startSession({ topic: 'Algebra' });

    expect(state.conversationId).toBe('abc-123');
    expect(state.metadata).toEqual({ topic: 'algebra' });
    expect(state.messages).toHaveLength(1);
    expect(state.learningObjectives).toEqual([
      {
        id: 'lo-1',
        title: 'Objective 1',
        description: 'Objective 1 description',
      },
    ]);
    expect(state.proposedBrief).toEqual({
      title: 'Algebra Foundations',
      description: 'Master key concepts',
      objectives: ['Understand variables'],
      notes: 'Focus on basics',
      level: 'Beginner',
    });
    expect(state.acceptedBrief).toBeNull();
    expect(state.resources).toEqual([
      {
        id: 'res-1',
        resourceType: 'file_upload',
        filename: 'algebra-notes.pdf',
        sourceUrl: null,
        fileSize: 1024,
        createdAt: '2024-01-02T00:00:00Z',
        previewText: 'These are algebra notes.',
      },
    ]);
    expect(state.uncoveredLearningObjectiveIds).toEqual(['lo-2']);
  });

  it('handles brief acceptance', async () => {
    mockRequest.mockResolvedValueOnce({
      conversation_id: 'abc-123',
      metadata: {},
      messages: [],
      proposed_brief: null,
      accepted_brief: null,
    });
    mockRequest.mockResolvedValueOnce({
      conversation_id: 'abc-123',
      metadata: { accepted_brief: { title: 'Accepted' } },
      messages: [],
      proposed_brief: null,
      accepted_brief: { title: 'Accepted', description: '', objectives: [] },
    });

    const repo = new LearningCoachRepo();
    const start = await repo.startSession({});
    const accepted = await repo.acceptBrief({
      conversationId: start.conversationId,
      brief: { title: 'Accepted', description: '', objectives: [] },
    });

    expect(accepted.acceptedBrief).toEqual({
      title: 'Accepted',
      description: '',
      objectives: [],
      notes: null,
      level: null,
    });
  });

  it('attaches a resource to the conversation', async () => {
    mockRequest.mockResolvedValueOnce({
      conversation_id: 'conv-1',
      metadata: {},
      messages: [],
      proposed_brief: null,
      accepted_brief: null,
      resources: [],
    });

    const repo = new LearningCoachRepo();
    const state = await repo.startSession({});

    mockRequest.mockResolvedValueOnce({
      conversation_id: state.conversationId,
      metadata: {},
      messages: [],
      proposed_brief: null,
      accepted_brief: null,
      resources: [
        {
          id: 'resource-9',
          resource_type: 'url',
          filename: null,
          source_url: 'https://example.com',
          file_size: null,
          created_at: '2024-04-02T00:00:00Z',
          preview_text: 'Example summary',
        },
      ],
    });

    const updated = await repo.attachResource({
      conversationId: state.conversationId,
      resourceId: 'resource-9',
    });

    expect(mockRequest).toHaveBeenLastCalledWith(
      `/api/v1/learning_conversations/coach/conversations/${encodeURIComponent(state.conversationId)}/resources`,
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ resource_id: 'resource-9', user_id: null }),
      })
    );
    expect(updated.resources).toEqual([
      {
        id: 'resource-9',
        resourceType: 'url',
        filename: null,
        sourceUrl: 'https://example.com',
        fileSize: null,
        createdAt: '2024-04-02T00:00:00Z',
        previewText: 'Example summary',
      },
    ]);
  });

  it('passes conversationId when accepting a brief', async () => {
    mockRequest
      .mockResolvedValueOnce({
        conversation_id: 'conv-9',
        metadata: {},
        messages: [],
      })
      .mockResolvedValueOnce({
        conversation_id: 'conv-9',
        metadata: {},
        messages: [],
        accepted_brief: null,
      });

    const repo = new LearningCoachRepo();
    const state = await repo.startSession({});

    await repo.acceptBrief({
      conversationId: state.conversationId,
      brief: { title: 'Test', description: '', objectives: [] },
    });

    expect(mockRequest).toHaveBeenNthCalledWith(
      2,
      '/api/v1/learning_conversations/coach/session/accept',
      expect.objectContaining({
        body: JSON.stringify({
          conversation_id: 'conv-9',
          brief: { title: 'Test', description: '', objectives: [] },
          user_id: null,
        }),
      })
    );
  });

  it('maps teaching assistant session state to DTO', async () => {
    mockRequest.mockResolvedValueOnce({
      conversation_id: 'ta-conv',
      unit_id: 'unit-1',
      lesson_id: 'lesson-1',
      session_id: 'session-1',
      metadata: { topic: 'fractions' },
      messages: [
        {
          id: 'msg-1',
          role: 'assistant',
          content: 'Hello from the assistant',
          created_at: '2024-02-01T00:00:00Z',
          metadata: {},
          suggested_quick_replies: ['Give me a hint', 'Show an example'],
        },
      ],
      suggested_quick_replies: ['Continue lesson'],
      context: {
        unit_id: 'unit-1',
        lesson_id: 'lesson-1',
        session_id: 'session-1',
        session: { progress_percentage: 40 },
        exercise_attempt_history: [{ exercise_id: 'ex-1', is_correct: false }],
        lesson: { title: 'Lesson 1' },
        unit: { title: 'Algebra Unit' },
        unit_session: { id: 'us-1' },
        unit_resources: [{ id: 'res-1' }],
      },
    });

    const repo = new LearningCoachRepo();
    const state = await repo.startTeachingAssistantSession({
      unitId: 'unit-1',
      lessonId: 'lesson-1',
      sessionId: 'session-1',
    });

    expect(state.conversationId).toBe('ta-conv');
    expect(state.unitId).toBe('unit-1');
    expect(state.messages[0].suggestedQuickReplies).toEqual([
      'Give me a hint',
      'Show an example',
    ]);
    expect(state.suggestedQuickReplies).toEqual(['Continue lesson']);
    expect(state.context.lesson?.title).toBe('Lesson 1');
    expect(state.context.unitResources).toEqual([{ id: 'res-1' }]);
  });

  it('includes query parameters when fetching teaching assistant session state', async () => {
    mockRequest.mockResolvedValueOnce({
      conversation_id: 'ta-conv',
      unit_id: 'unit-1',
      lesson_id: 'lesson-1',
      session_id: 'session-1',
      metadata: {},
      messages: [],
      context: {
        unit_id: 'unit-1',
        lesson_id: 'lesson-1',
        session_id: 'session-1',
      },
    });

    const repo = new LearningCoachRepo();
    await repo.getTeachingAssistantSessionState({
      conversationId: 'ta-conv',
      unitId: 'unit-1',
      lessonId: 'lesson-1',
      sessionId: 'session-1',
      userId: '99',
    });

    expect(mockRequest).toHaveBeenLastCalledWith(
      '/api/v1/learning_conversations/teaching_assistant/ta-conv?unit_id=unit-1&lesson_id=lesson-1&session_id=session-1&user_id=99',
      expect.objectContaining({ method: 'GET' })
    );
  });
});

describe('LearningCoachService (teaching assistant)', () => {
  const exampleState = {
    conversationId: 'conv-service',
    unitId: 'unit-service',
    lessonId: 'lesson-service',
    sessionId: 'session-service',
    messages: [],
    suggestedQuickReplies: [],
    metadata: {},
    context: {
      unitId: 'unit-service',
      lessonId: 'lesson-service',
      sessionId: 'session-service',
      session: null,
      exerciseAttemptHistory: [],
      lesson: null,
      unit: null,
      unitSession: null,
      unitResources: [],
    },
  } as TeachingAssistantSessionState;

  it('delegates startTeachingAssistantSession', async () => {
    const repo = {
      startTeachingAssistantSession: jest.fn().mockResolvedValue(exampleState),
    } as unknown as LearningCoachRepo;

    const service = new LearningCoachService(repo);
    const payload = {
      unitId: 'unit-service',
      lessonId: 'lesson-service',
      sessionId: 'session-service',
      userId: '55',
    };

    const result = await service.startTeachingAssistantSession(payload);

    expect(repo.startTeachingAssistantSession).toHaveBeenCalledWith(payload);
    expect(result).toBe(exampleState);
  });

  it('delegates submitTeachingAssistantQuestion', async () => {
    const repo = {
      submitTeachingAssistantQuestion: jest
        .fn()
        .mockResolvedValue(exampleState),
    } as unknown as LearningCoachRepo;

    const service = new LearningCoachService(repo);
    const payload = {
      conversationId: 'conv-service',
      message: 'How do I do this?',
      unitId: 'unit-service',
      lessonId: 'lesson-service',
      sessionId: 'session-service',
      userId: '55',
    };

    const result = await service.submitTeachingAssistantQuestion(payload);

    expect(repo.submitTeachingAssistantQuestion).toHaveBeenCalledWith(payload);
    expect(result).toBe(exampleState);
  });

  it('delegates getTeachingAssistantSessionState', async () => {
    const repo = {
      getTeachingAssistantSessionState: jest
        .fn()
        .mockResolvedValue(exampleState),
    } as unknown as LearningCoachRepo;

    const service = new LearningCoachService(repo);
    const payload = {
      conversationId: 'conv-service',
      unitId: 'unit-service',
      lessonId: 'lesson-service',
      sessionId: 'session-service',
      userId: '55',
    };

    const result = await service.getTeachingAssistantSessionState(payload);

    expect(repo.getTeachingAssistantSessionState).toHaveBeenCalledWith(payload);
    expect(result).toBe(exampleState);
  });
});
