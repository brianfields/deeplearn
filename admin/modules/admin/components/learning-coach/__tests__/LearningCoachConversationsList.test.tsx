import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import type { LearningCoachConversationsListResponse } from '../../../models';
import { LearningCoachConversationsList } from '../LearningCoachConversationsList';

const mockUseLearningCoachConversations = vi.fn();
const mockUseLearningCoachFilters = vi.fn();
const mockUseAdminStore = vi.fn();

vi.mock('next/link', () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock('../../../queries', () => ({
  useLearningCoachConversations: (params?: unknown) =>
    mockUseLearningCoachConversations(params),
}));

vi.mock('../../../store', () => ({
  useLearningCoachFilters: () => mockUseLearningCoachFilters(),
  useAdminStore: (selector: (state: { setLearningCoachFilters: (filters: unknown) => void }) => unknown) =>
    mockUseAdminStore(selector),
}));

describe('LearningCoachConversationsList', () => {
  const setLearningCoachFilters = vi.fn();
  const defaultResponse: Partial<ReturnType<typeof mockUseLearningCoachConversations>> = {
    data: undefined,
    isLoading: false,
    error: undefined,
    refetch: vi.fn(),
  };

  beforeEach(() => {
    mockUseLearningCoachFilters.mockReturnValue({ limit: 20, offset: 0 });
    mockUseAdminStore.mockImplementation((selector) =>
      selector({ setLearningCoachFilters })
    );
    mockUseLearningCoachConversations.mockReturnValue(defaultResponse);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders a loading spinner while conversations load', () => {
    mockUseLearningCoachConversations.mockReturnValue({
      ...defaultResponse,
      isLoading: true,
    });

    render(<LearningCoachConversationsList />);

    expect(screen.getByText('Loading conversations...')).toBeInTheDocument();
  });

  it('renders an error state with retry action', () => {
    const refetch = vi.fn();
    mockUseLearningCoachConversations.mockReturnValue({
      ...defaultResponse,
      error: new Error('Network error'),
      refetch,
    });

    render(<LearningCoachConversationsList />);

    expect(
      screen.getByText('Failed to load conversations. Please try again.')
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(refetch).toHaveBeenCalled();
  });

  it('renders the conversations table and handles pagination controls', () => {
    const now = new Date('2024-06-01T12:00:00Z');
    const response: LearningCoachConversationsListResponse = {
      conversations: [
        {
          id: 'conv_1',
          user_id: 'user-1',
          title: 'Initial title',
          message_count: 5,
          created_at: now,
          updated_at: now,
          last_message_at: now,
          metadata: {
            topic: 'Quantum Mechanics Deep Dive',
            accepted_at: now.toISOString(),
            accepted_brief: { title: 'Quantum Mechanics Unit' },
          },
        },
        {
          id: 'conv_2',
          user_id: null,
          title: null,
          message_count: 3,
          created_at: now,
          updated_at: now,
          last_message_at: now,
          metadata: {
            topic: 'Linear Algebra Refresher',
          },
        },
      ],
      limit: 2,
      offset: 0,
      has_next: true,
    };

    mockUseLearningCoachFilters.mockReturnValue({ limit: 2, offset: 0 });
    mockUseLearningCoachConversations.mockReturnValue({
      ...defaultResponse,
      data: response,
    });

    render(<LearningCoachConversationsList />);

    expect(
      screen.getByText('Showing conversations 1 – 2')
    ).toBeInTheDocument();
    expect(screen.getByText('Quantum Mechanics Deep Dive')).toBeInTheDocument();
    expect(screen.getByText('Linear Algebra Refresher')).toBeInTheDocument();
    expect(screen.getAllByText('View transcript')).toHaveLength(2);
    expect(screen.getByText('Accepted')).toBeInTheDocument();

    const nextButton = screen.getByRole('button', { name: 'Next' });
    expect(nextButton).toBeEnabled();
    fireEvent.click(nextButton);
    expect(setLearningCoachFilters).toHaveBeenCalledWith({ offset: 2 });

    const select = screen.getByLabelText('Per page:');
    fireEvent.change(select, { target: { value: '50' } });
    expect(setLearningCoachFilters).toHaveBeenCalledWith({ limit: 50, offset: 0 });
  });
});
