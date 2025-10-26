import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { TaskStatus } from './models';
import { AdminService } from './service';

const mocks = vi.hoisted(() => ({
  tasksMock: vi.fn<(limit?: number, queueName?: string) => Promise<any[]>>(),
  taskByIdMock: vi.fn<(taskId: string) => Promise<any>>(),
  taskFlowRunsMock: vi.fn<(taskId: string) => Promise<any[]>>(),
  unitFlowRunsMock: vi.fn<(unitId: string) => Promise<any[]>>(),
  conversationListMock: vi.fn<(
    params?: any
  ) => Promise<{
    conversations: any[];
    total_count: number;
    page: number;
    page_size: number;
    has_next: boolean;
  }>>(),
  conversationDetailMock: vi.fn<(conversationId: string) => Promise<any>>(),
  learningSessionListMock: vi.fn<(
    params?: any
  ) => Promise<{
    sessions: any[];
    total_count: number;
    page: number;
    page_size: number;
    has_next: boolean;
  }>>(),
  learningSessionDetailMock: vi.fn<(sessionId: string) => Promise<any>>(),
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
    conversations: {
      list: mocks.conversationListMock,
      byId: mocks.conversationDetailMock,
    },
    learningSessions: {
      list: mocks.learningSessionListMock,
      byId: mocks.learningSessionDetailMock,
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

  it('maps conversation summaries into DTOs with pagination metadata', async () => {
    const summary = {
      id: 'conv-1',
      user_id: 42,
      title: 'Algebra coaching',
      status: 'active',
      message_count: 5,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:05:00Z',
      last_message_at: '2024-01-01T00:04:00Z',
      metadata: { topic: 'algebra' },
    };

    mocks.conversationListMock.mockResolvedValueOnce({
      conversations: [summary],
      total_count: 1,
      page: 1,
      page_size: 50,
      has_next: false,
    });

    const result = await service.getConversations({ page: 1, page_size: 50 });

    expect(mocks.conversationListMock).toHaveBeenCalledWith({ page: 1, page_size: 50 });
    expect(result.total_count).toBe(1);
    expect(result.page_size).toBe(50);
    expect(result.conversations).toHaveLength(1);
    expect(result.conversations[0].id).toBe('conv-1');
    expect(result.conversations[0].created_at).toEqual(new Date('2024-01-01T00:00:00Z'));
    expect(result.conversations[0].metadata.topic).toBe('algebra');
  });

  it('maps conversation detail with messages into DTO', async () => {
    const detail = {
      conversation_id: 'conv-1',
      metadata: { topic: 'algebra' },
      proposed_brief: null,
      accepted_brief: null,
      messages: [
        {
          id: 'msg-1',
          role: 'user',
          content: 'Hello',
          created_at: '2024-01-01T00:00:00Z',
          metadata: { source: 'student' },
          tokens_used: 120,
          cost_estimate: 0.0025,
          llm_request_id: 'req-1',
          message_order: 1,
        },
      ],
    };

    mocks.conversationDetailMock.mockResolvedValueOnce(detail);

    const result = await service.getConversation('conv-1');

    expect(mocks.conversationDetailMock).toHaveBeenCalledWith('conv-1');
    expect(result).not.toBeNull();
    expect(result?.conversation_id).toBe('conv-1');
    expect(result?.messages).toHaveLength(1);
    expect(result?.messages[0].tokens_used).toBe(120);
    expect(result?.messages[0].metadata.source).toBe('student');
  });

  it('maps learning sessions into DTOs', async () => {
    const response = {
      sessions: [
        {
          id: 'session-1',
          lesson_id: 'lesson-1',
          unit_id: 'unit-1',
          user_id: 'user-1',
          status: 'completed',
          started_at: '2024-01-01T00:00:00Z',
          completed_at: '2024-01-01T00:30:00Z',
          current_exercise_index: 3,
          total_exercises: 5,
          progress_percentage: 60,
          session_data: { exercise_answers: {} },
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 25,
      has_next: false,
    };

    mocks.learningSessionListMock.mockResolvedValueOnce(response);

    const result = await service.getLearningSessions({ page: 1, page_size: 25 });

    expect(mocks.learningSessionListMock).toHaveBeenCalledWith({ page: 1, page_size: 25 });
    expect(result.sessions).toHaveLength(1);
    expect(result.total_count).toBe(1);
    expect(result.sessions[0].id).toBe('session-1');
    expect(result.sessions[0].started_at).toEqual(new Date('2024-01-01T00:00:00Z'));
  });

  it('returns null when learning session detail fetch fails', async () => {
    mocks.learningSessionDetailMock.mockRejectedValueOnce(new Error('network error'));

    const detail = await service.getLearningSession('session-1');

    expect(mocks.learningSessionDetailMock).toHaveBeenCalledWith('session-1');
    expect(detail).toBeNull();
  });
});
