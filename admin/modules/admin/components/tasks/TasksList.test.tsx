import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import type { TaskStatus } from '../../models';
import { TasksList } from './TasksList';
import { useTasks } from '../../queries';

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
  });

  it('renders empty state and triggers reload', () => {
    const refetch = vi.fn();
    useTasksMock.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch,
    } as any);

    render(
      <TasksList selectedTaskId={null} onSelectTask={vi.fn()} />
    );

    expect(screen.getByText('No background tasks found.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /reload/i }));
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it('renders tasks and allows selecting a task', () => {
    const refetch = vi.fn();
    const handleSelect = vi.fn();
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
      <TasksList selectedTaskId="task-2" onSelectTask={handleSelect} />
    );

    expect(screen.getByText('generate_unit')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Unit unit-1' })).toHaveAttribute('href', '/units/unit-1');

    const reloadButtons = screen.getAllByRole('button', { name: /reload/i });
    fireEvent.click(reloadButtons[0]);
    expect(refetch).toHaveBeenCalledTimes(1);

    const taskTypeCell = screen.getByText('generate_unit');
    fireEvent.click(taskTypeCell.closest('tr')!);
    expect(handleSelect).toHaveBeenCalledWith('task-1');
  });
});
