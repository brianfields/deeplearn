import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { TaskStatus } from './models';
import { AdminService } from './service';

const mocks = vi.hoisted(() => ({
  tasksMock: vi.fn<(limit?: number, queueName?: string) => Promise<any[]>>(),
  taskByIdMock: vi.fn<(taskId: string) => Promise<any>>(),
  taskFlowRunsMock: vi.fn<(taskId: string) => Promise<any[]>>(),
  unitFlowRunsMock: vi.fn<(unitId: string) => Promise<any[]>>(),
}));

vi.mock('./repo', () => ({
  AdminRepo: {
    taskQueue: {
      tasks: mocks.tasksMock,
      taskById: mocks.taskByIdMock,
      flowRuns: mocks.taskFlowRunsMock,
    },
    units: {
      flowRuns: mocks.unitFlowRunsMock,
    },
  },
}));

describe('AdminService task and flow mappings', () => {
  const service = new AdminService();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('maps tasks with missing optional fields to DTO defaults', async () => {
    const apiTask = {
      task_id: 'task-001',
      status: 'pending',
      created_at: '2024-01-01T00:00:00Z',
      queue_name: 'default',
    };

    mocks.tasksMock.mockResolvedValueOnce([apiTask]);

    const result = await service.getTasks(25);

    expect(mocks.tasksMock).toHaveBeenCalledWith(25, undefined);
    expect(result).toHaveLength(1);

    const task: TaskStatus = result[0];
    expect(task.task_id).toBe('task-001');
    expect(task.status).toBe('pending');
    expect(task.queue_name).toBe('default');
    expect(task.priority).toBe(0);
    expect(task.retry_count).toBe(0);
    expect(task.error_message).toBeNull();
    expect(task.result).toBeNull();
    expect(task.submitted_at).toEqual(new Date('2024-01-01T00:00:00Z'));
    expect(task.created_at).toEqual(new Date('2024-01-01T00:00:00Z'));
    expect(task.started_at).toBeNull();
    expect(task.completed_at).toBeNull();
    expect(task.flow_name).toBeNull();
    expect(task.task_type).toBeNull();
    expect(task.progress_percentage).toBeNull();
    expect(task.current_step).toBeNull();
    expect(task.worker_id).toBeNull();
    expect(task.user_id).toBeNull();
    expect(task.flow_run_id).toBeNull();
    expect(task.unit_id).toBeNull();
  });

  it('maps flow runs associated with a task', async () => {
    const apiFlowRun = {
      id: 'flow-123',
      flow_name: 'unit_generation',
      status: 'completed',
      execution_mode: 'background',
      arq_task_id: 'task-001',
      user_id: 'user-1',
      created_at: '2024-01-01T00:00:00Z',
      started_at: '2024-01-01T00:05:00Z',
      completed_at: '2024-01-01T00:06:00Z',
      execution_time_ms: 60000,
      total_tokens: 1200,
      total_cost: 1.5,
      step_count: 5,
      error_message: null,
    };

    mocks.taskFlowRunsMock.mockResolvedValueOnce([apiFlowRun]);

    const runs = await service.getTaskFlowRuns('task-001');

    expect(mocks.taskFlowRunsMock).toHaveBeenCalledWith('task-001');
    expect(runs).toHaveLength(1);
    expect(runs[0].id).toBe('flow-123');
    expect(runs[0].started_at).toEqual(new Date('2024-01-01T00:05:00Z'));
    expect(runs[0].completed_at).toEqual(new Date('2024-01-01T00:06:00Z'));
    expect(runs[0].execution_time_ms).toBe(60000);
    expect(runs[0].total_tokens).toBe(1200);
  });

  it('returns [] when unit flow run lookup fails', async () => {
    mocks.unitFlowRunsMock.mockRejectedValueOnce(new Error('network error'));

    const runs = await service.getUnitFlowRuns('unit-123');

    expect(mocks.unitFlowRunsMock).toHaveBeenCalledWith('unit-123');
    expect(runs).toEqual([]);
  });
});
