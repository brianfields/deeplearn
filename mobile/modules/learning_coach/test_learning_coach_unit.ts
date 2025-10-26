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
});
