import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import type { TaskStatus } from '../../models';
import { TasksList } from './TasksList';
import { useTasks } from '../../queries';

const pushMock = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: pushMock,
    prefetch: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
}));

vi.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: any) => (
    <a href={typeof href === 'string' ? href : '#'} {...rest}>
      {children}
    </a>
  ),
}));

vi.mock('../../queries', () => ({
  useTasks: vi.fn(),
}));

const useTasksMock = vi.mocked(useTasks);

describe('TasksList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    pushMock.mockReset();
  });

  it('renders empty state when no tasks are returned', () => {
    const refetch = vi.fn();
    useTasksMock.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch,
    } as any);

    render(
      <TasksList />
    );

    expect(screen.getByText('No background tasks found.')).toBeInTheDocument();
    expect(refetch).not.toHaveBeenCalled();
  });

  it('renders tasks and allows selecting a task', () => {
    const refetch = vi.fn();
    const baseDates = {
      submitted: new Date('2024-01-01T00:00:00Z'),
      started: new Date('2024-01-01T00:05:00Z'),
      completed: new Date('2024-01-01T00:05:05Z'),
    };

    const tasks: TaskStatus[] = [
      {
        task_id: 'task-1',
        status: 'completed',
        submitted_at: baseDates.submitted,
        created_at: baseDates.submitted,
        started_at: baseDates.started,
        completed_at: baseDates.completed,
        retry_count: 0,
        error_message: null,
        result: null,
        queue_name: 'default',
        priority: 0,
        task_type: 'generate_unit',
        flow_name: 'unit_flow',
        progress_percentage: null,
        current_step: null,
        worker_id: null,
        user_id: null,
        flow_run_id: null,
        unit_id: 'unit-1',
      },
      {
        task_id: 'task-2',
        status: 'running',
        submitted_at: baseDates.submitted,
        created_at: baseDates.submitted,
        started_at: baseDates.started,
        completed_at: null,
        retry_count: 1,
        error_message: 'Needs attention',
        result: null,
        queue_name: 'default',
        priority: 1,
        task_type: 'reprocess',
        flow_name: null,
        progress_percentage: 25,
        current_step: 'prepare',
        worker_id: 'worker-1',
        user_id: 'user-1',
        flow_run_id: 'flow-1',
        unit_id: null,
      },
    ];

    useTasksMock.mockReturnValue({
      data: tasks,
      isLoading: false,
      error: null,
      refetch,
    } as any);

    render(
      <TasksList />
    );

    expect(screen.getByText('generate_unit')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Unit unit-1' })).toHaveAttribute('href', '/units/unit-1');

    const taskTypeCell = screen.getByText('generate_unit');
    fireEvent.click(taskTypeCell.closest('tr')!);
    expect(pushMock).toHaveBeenCalledWith('/tasks/task-1');
  });
});
