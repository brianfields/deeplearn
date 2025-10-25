import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import type { TaskStatus, FlowRunSummary } from '../../models';
import { TaskDetails } from './TaskDetails';
import { useTask, useTaskFlowRuns } from '../../queries';

vi.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: any) => (
    <a href={typeof href === 'string' ? href : '#'} {...rest}>
      {children}
    </a>
  ),
}));

vi.mock('../../queries', () => ({
  useTask: vi.fn(),
  useTaskFlowRuns: vi.fn(),
}));

const useTaskMock = vi.mocked(useTask);
const useTaskFlowRunsMock = vi.mocked(useTaskFlowRuns);

describe('TaskDetails', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('prompts for selection when no task is chosen', () => {
    useTaskMock.mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as any);
    useTaskFlowRunsMock.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    render(<TaskDetails taskId={null} />);

    expect(screen.getByText('Select a task to see details.')).toBeInTheDocument();
  });

  it('shows error message and retries both queries', () => {
    const refetchTask = vi.fn();
    const refetchFlows = vi.fn();

    useTaskMock.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('boom'),
      refetch: refetchTask,
    } as any);
    useTaskFlowRunsMock.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch: refetchFlows,
    } as any);

    render(<TaskDetails taskId="task-9" />);

    fireEvent.click(screen.getByRole('button', { name: /try again/i }));

    expect(refetchTask).toHaveBeenCalledTimes(1);
    expect(refetchFlows).toHaveBeenCalledTimes(1);
  });

  it('renders task metadata, flow runs, and reload actions', () => {
    const refetchTask = vi.fn();
    const refetchFlows = vi.fn();

    const task: TaskStatus = {
      task_id: 'task-1',
      status: 'completed',
      submitted_at: new Date('2024-01-01T00:00:00Z'),
      created_at: new Date('2024-01-01T00:00:00Z'),
      started_at: new Date('2024-01-01T00:05:00Z'),
      completed_at: new Date('2024-01-01T00:05:05Z'),
      retry_count: 0,
      error_message: null,
      result: null,
      queue_name: 'default',
      priority: 0,
      flow_name: 'unit_flow',
      task_type: 'generate_unit',
      progress_percentage: 100,
      current_step: null,
      worker_id: 'worker-1',
      user_id: 'user-1',
      flow_run_id: 'flow-1',
      unit_id: 'unit-1',
    };

    const flowRun: FlowRunSummary = {
      id: 'flow-1',
      flow_name: 'unit_flow',
      status: 'completed',
      execution_mode: 'background',
      arq_task_id: 'task-1',
      unit_id: 'unit-1',
      user_id: 'user-1',
      created_at: new Date('2024-01-01T00:00:00Z'),
      started_at: new Date('2024-01-01T00:05:00Z'),
      completed_at: new Date('2024-01-01T00:05:10Z'),
      execution_time_ms: 2000,
      total_tokens: 1500,
      total_cost: 2.5,
      step_count: 4,
      error_message: null,
    };

    useTaskMock.mockReturnValue({
      data: task,
      isLoading: false,
      error: null,
      refetch: refetchTask,
    } as any);
    useTaskFlowRunsMock.mockReturnValue({
      data: [flowRun],
      isLoading: false,
      error: null,
      refetch: refetchFlows,
    } as any);

    render(<TaskDetails taskId="task-1" />);

    expect(screen.getByText('Task Details')).toBeInTheDocument();
    expect(screen.getByText('task-1')).toBeInTheDocument();
    expect(screen.getAllByText('unit_flow')[0]).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'View' })).toHaveAttribute('href', '/flows/flow-1');

    fireEvent.click(screen.getByRole('button', { name: 'Reload' }));
    expect(refetchTask).toHaveBeenCalledTimes(1);
    expect(refetchFlows).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: 'Reload flows' }));
    expect(refetchFlows).toHaveBeenCalledTimes(2);
  });
});
