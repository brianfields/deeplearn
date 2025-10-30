import { ContentCreatorRepo } from './repo';
import type { UnitCreationRequest } from './models';

const mockRequest = jest.fn();

jest.mock('../infrastructure/public', () => ({
  infrastructureProvider: jest.fn(() => ({
    request: mockRequest,
  })),
}));

describe('ContentCreatorRepo', () => {
  beforeEach(() => {
    mockRequest.mockReset();
  });

  it('includes conversation_id when creating a unit from a conversation', async () => {
    mockRequest.mockResolvedValue({
      unit_id: 'unit-123',
      status: 'in_progress',
      title: 'My Unit',
    });

    const repo = new ContentCreatorRepo();
    const request: UnitCreationRequest = {
      topic: 'Physics',
      difficulty: 'intermediate',
      targetLessonCount: 5,
      ownerUserId: 42,
      conversationId: 'conv-abc',
    };

    const response = await repo.createUnit(request);

    expect(response).toEqual({
      unitId: 'unit-123',
      status: 'in_progress',
      title: 'My Unit',
    });

    expect(mockRequest).toHaveBeenCalledWith(
      '/api/v1/content-creator/units?user_id=42',
      expect.objectContaining({
        method: 'POST',
      })
    );

    const [, options] = mockRequest.mock.calls[0];
    const body = JSON.parse((options as { body: string }).body);
    expect(body).toEqual({
      topic: 'Physics',
      difficulty: 'intermediate',
      target_lesson_count: 5,
      conversation_id: 'conv-abc',
    });
  });
});
