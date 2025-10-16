import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import type { LearningCoachConversationDetail as ConversationDetailType } from '../../../models';
import { LearningCoachConversationDetail } from '../LearningCoachConversationDetail';

const mockUseLearningCoachConversation = vi.fn();

vi.mock('next/link', () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock('../../../queries', () => ({
  useLearningCoachConversation: (conversationId: string) =>
    mockUseLearningCoachConversation(conversationId),
}));

describe('LearningCoachConversationDetail', () => {
  const refetch = vi.fn();

  beforeEach(() => {
    mockUseLearningCoachConversation.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: undefined,
      refetch,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('shows a loading spinner while fetching', () => {
    mockUseLearningCoachConversation.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: undefined,
      refetch,
    });

    render(<LearningCoachConversationDetail conversationId="conv_loading" />);

    expect(screen.getByText('Loading conversation...')).toBeInTheDocument();
  });

  it('renders an error state and allows retry', () => {
    mockUseLearningCoachConversation.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Oops'),
      refetch,
    });

    render(<LearningCoachConversationDetail conversationId="conv_error" />);

    expect(screen.getByText('Failed to load conversation. Please try again.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(refetch).toHaveBeenCalled();
  });

  it('renders transcript, briefs, and metadata for a conversation', () => {
    const now = new Date('2024-06-10T09:30:00Z');
    const detail: ConversationDetailType = {
      conversation_id: 'conv_123',
      metadata: {
        topic: 'Project-based AI course',
        accepted_at: now.toISOString(),
        user_id: 'learner-9',
      },
      proposed_brief: {
        title: 'AI for Makers',
        description: 'Hands-on curriculum exploring applied ML concepts.',
        objectives: ['Prototype with vision models', 'Deploy tinyML workloads'],
        notes: 'Include weekend build checkpoints',
        level: 'Intermediate',
        raw: {
          title: 'AI for Makers',
        },
      },
      accepted_brief: {
        title: 'AI for Makers (Accepted)',
        description: 'Refined plan focusing on robotics applications.',
        objectives: ['Calibrate sensors', 'Deploy control loops'],
        notes: null,
        level: 'Intermediate',
        raw: {
          accepted: true,
        },
      },
      messages: [
        {
          id: 'm1',
          role: 'assistant',
          content: 'Welcome! What would you like to learn today?',
          created_at: now,
          metadata: {},
        },
        {
          id: 'm2',
          role: 'user',
          content: 'I want a project-based AI course with hands-on builds.',
          created_at: new Date('2024-06-10T09:31:00Z'),
          metadata: { mood: 'excited' },
        },
      ],
    };

    mockUseLearningCoachConversation.mockReturnValue({
      data: detail,
      isLoading: false,
      error: undefined,
      refetch,
    });

    render(<LearningCoachConversationDetail conversationId="conv_123" />);

    expect(screen.getByText('Learning Coach Conversation')).toBeInTheDocument();
    expect(screen.getByText('AI for Makers')).toBeInTheDocument();
    expect(screen.getByText('AI for Makers (Accepted)')).toBeInTheDocument();
    expect(screen.getByText('Learning Coach')).toBeInTheDocument();
    expect(
      screen.getByText('Welcome! What would you like to learn today?')
    ).toBeInTheDocument();
    expect(
      screen.getByText('I want a project-based AI course with hands-on builds.')
    ).toBeInTheDocument();
    expect(screen.getByText('Learner ID')).toBeInTheDocument();
    expect(screen.getByText('learner-9')).toBeInTheDocument();
    expect(screen.getByText('Accepted')).toBeInTheDocument();
  });
});
