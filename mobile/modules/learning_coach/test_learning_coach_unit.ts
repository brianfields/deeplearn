import { LearningCoachRepo } from './repo';

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
      `/api/v1/learning_coach/conversations/${encodeURIComponent(state.conversationId)}/resources`,
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
      '/api/v1/learning_coach/session/accept',
      expect.objectContaining({
        body: JSON.stringify({
          conversation_id: 'conv-9',
          brief: { title: 'Test', description: '', objectives: [] },
          user_id: null,
        }),
      })
    );
  });
});
