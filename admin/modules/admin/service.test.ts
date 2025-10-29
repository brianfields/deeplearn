import { describe, it, expect, beforeEach, vi } from 'vitest';
import type {
  TaskStatus,
  ConversationSummary,
  LessonSummary,
  ResourceWithUsage,
  UserDetail,
} from './models';
import { AdminService } from './service';

const mocks = vi.hoisted(() => ({
  tasks: vi.fn(),
  taskById: vi.fn(),
  taskFlowRuns: vi.fn(),
  unitFlowRuns: vi.fn(),
  unitDetail: vi.fn(),
  unitResources: vi.fn(),
  conversationList: vi.fn(),
  conversationDetail: vi.fn(),
  lessonsList: vi.fn(),
  lessonById: vi.fn(),
  resourcesByUser: vi.fn(),
  usersDetail: vi.fn(),
  usersUpdate: vi.fn(),
  usersList: vi.fn(),
  unitsList: vi.fn(),
  unitsBasics: vi.fn(),
  healthCheck: vi.fn(),
}));

vi.mock('./repo', () => ({
  AdminRepo: {
    taskQueue: {
      tasks: mocks.tasks,
      taskById: mocks.taskById,
      flowRuns: mocks.taskFlowRuns,
    },
    units: {
      list: mocks.unitsList,
      basics: mocks.unitsBasics,
      detail: mocks.unitDetail,
      flowRuns: mocks.unitFlowRuns,
      resources: mocks.unitResources,
    },
    conversations: {
      list: mocks.conversationList,
      byId: mocks.conversationDetail,
    },
    lessons: {
      list: mocks.lessonsList,
      byId: mocks.lessonById,
    },
    resources: {
      listByUser: mocks.resourcesByUser,
    },
    users: {
      list: mocks.usersList,
      detail: mocks.usersDetail,
      update: mocks.usersUpdate,
    },
    metrics: {
      getSystemMetrics: vi.fn(),
      getFlowMetrics: vi.fn(),
      getDailyMetrics: vi.fn(),
    },
    flows: {
      list: vi.fn(),
      getStepDetails: vi.fn(),
    },
    flowEngine: {
      byId: vi.fn(),
    },
    llmRequests: {
      list: vi.fn(),
      byId: vi.fn(),
    },
    learningSessions: {
      list: vi.fn(),
      byId: vi.fn(),
    },
    healthCheck: mocks.healthCheck,
  },
}));

describe('AdminService resource-aware mappings', () => {
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

    mocks.tasks.mockResolvedValueOnce([apiTask]);

    const result = await service.getTasks(25);

    expect(mocks.tasks).toHaveBeenCalledWith(25, undefined);
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

    mocks.taskFlowRuns.mockResolvedValueOnce([apiFlowRun]);

    const runs = await service.getTaskFlowRuns('task-001');

    expect(mocks.taskFlowRuns).toHaveBeenCalledWith('task-001');
    expect(runs).toHaveLength(1);
    expect(runs[0].id).toBe('flow-123');
    expect(runs[0].started_at).toEqual(new Date('2024-01-01T00:05:00Z'));
    expect(runs[0].completed_at).toEqual(new Date('2024-01-01T00:06:00Z'));
    expect(runs[0].execution_time_ms).toBe(60000);
  });

  it('returns [] when unit flow run lookup fails', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mocks.unitFlowRuns.mockRejectedValueOnce(new Error('network error'));

    const runs = await service.getUnitFlowRuns('unit-123');

    expect(mocks.unitFlowRuns).toHaveBeenCalledWith('unit-123');
    expect(runs).toEqual([]);
    errorSpy.mockRestore();
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

    mocks.conversationList.mockResolvedValueOnce({
      conversations: [summary],
      total_count: 1,
      page: 1,
      page_size: 50,
      has_next: false,
    });

    const result = await service.getConversations({ page: 1, page_size: 50 });

    expect(mocks.conversationList).toHaveBeenCalledWith({ page: 1, page_size: 50 });
    expect(result.total_count).toBe(1);
    expect(result.page_size).toBe(50);
    expect(result.conversations).toHaveLength(1);

    const conversation: ConversationSummary = result.conversations[0];
    expect(conversation.id).toBe('conv-1');
    expect(conversation.created_at).toEqual(new Date('2024-01-01T00:00:00Z'));
    expect(conversation.metadata.topic).toBe('algebra');
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

    mocks.conversationDetail.mockResolvedValueOnce(detail);

    const result = await service.getConversation('conv-1');

    expect(mocks.conversationDetail).toHaveBeenCalledWith('conv-1');
    expect(result).not.toBeNull();
    expect(result?.conversation_id).toBe('conv-1');
    expect(result?.messages).toHaveLength(1);
    expect(result?.messages[0].tokens_used).toBe(120);
    expect(result?.messages[0].metadata.source).toBe('student');
  });

  it('maps lesson summaries with podcast metadata', async () => {
    mocks.lessonsList.mockResolvedValueOnce({
      lessons: [
        {
          id: 'lesson-1',
          title: 'Lesson One',
          learner_level: 'beginner',
          package_version: 1,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T01:00:00Z',
          has_podcast: true,
          podcast_voice: 'alloy',
          podcast_duration_seconds: 185,
          podcast_audio_url: '/audio/lesson-1.mp3',
          podcast_generated_at: '2024-01-01T01:10:00Z',
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 25,
      has_next: false,
    });

    const result = await service.getLessons();

    expect(mocks.lessonsList).toHaveBeenCalled();
    expect(result.lessons).toHaveLength(1);

    const summary: LessonSummary = result.lessons[0];
    expect(summary.has_podcast).toBe(true);
    expect(summary.podcast_voice).toBe('alloy');
    expect(summary.podcast_duration_seconds).toBe(185);
    expect(summary.podcast_audio_url).toBe('/audio/lesson-1.mp3');
    expect(summary.podcast_generated_at).toEqual(new Date('2024-01-01T01:10:00Z'));
  });

  it('maps lesson detail podcast metadata', async () => {
    mocks.lessonById.mockResolvedValueOnce({
      id: 'lesson-1',
      title: 'Lesson One',
      learner_level: 'beginner',
      source_material: 'Source',
      package: { exercises: [], mini_lesson: 'Mini lesson' },
      package_version: 1,
      flow_run_id: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T01:00:00Z',
      has_podcast: true,
      podcast_transcript: 'Lesson transcript',
      podcast_voice: 'alloy',
      podcast_audio_url: '/audio/lesson-1.mp3',
      podcast_duration_seconds: 200,
      podcast_generated_at: '2024-01-01T01:30:00Z',
    });

    const lesson = await service.getLesson('lesson-1');

    expect(mocks.lessonById).toHaveBeenCalledWith('lesson-1');
    expect(lesson?.has_podcast).toBe(true);
    expect(lesson?.podcast_transcript).toBe('Lesson transcript');
    expect(lesson?.podcast_voice).toBe('alloy');
    expect(lesson?.podcast_audio_url).toBe('/audio/lesson-1.mp3');
    expect(lesson?.podcast_duration_seconds).toBe(200);
    expect(lesson?.podcast_generated_at).toEqual(new Date('2024-01-01T01:30:00Z'));
  });

  it('maps unit detail including associated resources', async () => {
    mocks.unitDetail.mockResolvedValueOnce({
      id: 'unit-1',
      title: 'Unit One',
      description: null,
      learner_level: 'beginner',
      lesson_order: ['lesson-1'],
      lessons: [
        {
          id: 'lesson-1',
          title: 'Lesson One',
          learner_level: 'beginner',
          learning_objectives: [],
          key_concepts: [],
          exercise_count: 3,
          has_podcast: true,
          podcast_voice: 'verse',
          podcast_duration_seconds: 150,
          podcast_generated_at: '2024-01-02T00:00:00Z',
          podcast_audio_url: '/audio/lesson-1.mp3',
        },
      ],
      learning_objectives: [],
      target_lesson_count: 1,
      source_material: null,
      generated_from_topic: false,
      flow_type: 'standard',
      learning_objective_progress: null,
      has_podcast: true,
      podcast_voice: 'intro-voice',
      podcast_duration_seconds: 220,
      podcast_transcript: 'Intro transcript',
      podcast_audio_url: '/audio/unit-intro.mp3',
      art_image_url: null,
      art_image_description: null,
      status: 'completed',
      creation_progress: null,
      error_message: null,
      arq_task_id: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    });
    mocks.unitFlowRuns.mockResolvedValueOnce([]);
    mocks.unitResources.mockResolvedValueOnce([
      {
        id: 'res-1',
        resource_type: 'file',
        filename: 'notes.pdf',
        source_url: null,
        file_size: 1234,
        created_at: '2024-01-01T00:00:00Z',
        preview_text: 'Preview',
      },
    ]);

    const detail = await service.getUnitDetail('unit-1');

    expect(mocks.unitDetail).toHaveBeenCalledWith('unit-1');
    expect(detail).not.toBeNull();
    expect(detail?.lessons[0].podcast_voice).toBe('verse');
    expect(detail?.resources).toHaveLength(1);
    expect(detail?.resources[0].filename).toBe('notes.pdf');
  });

  it('builds user resources with usage lookups', async () => {
    const apiUser = {
      id: 99,
      email: 'learner@example.com',
      name: 'Learner',
      role: 'student',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
      associations: {
        owned_unit_count: 1,
        owned_global_unit_count: 0,
        learning_session_count: 0,
        llm_request_count: 0,
      },
      owned_units: [
        {
          id: 'unit-1',
          title: 'Unit One',
          is_global: false,
          updated_at: '2024-01-02T00:00:00Z',
          art_image_url: null,
          art_image_description: null,
        },
      ],
      recent_sessions: [],
      recent_llm_requests: [],
      recent_conversations: [],
    };

    mocks.usersDetail.mockResolvedValueOnce(apiUser);
    mocks.resourcesByUser.mockResolvedValueOnce([
      {
        id: 'res-1',
        resource_type: 'file',
        filename: 'notes.pdf',
        source_url: null,
        file_size: 1234,
        created_at: '2024-01-01T00:00:00Z',
        preview_text: 'Preview',
      },
    ]);
    mocks.unitResources.mockResolvedValueOnce([
      {
        id: 'res-1',
        resource_type: 'file',
        filename: 'notes.pdf',
        source_url: null,
        file_size: 1234,
        created_at: '2024-01-01T00:00:00Z',
        preview_text: 'Preview',
      },
    ]);

    const userDetail = await service.getUser(99);

    expect(mocks.usersDetail).toHaveBeenCalledWith(99);
    expect(mocks.resourcesByUser).toHaveBeenCalledWith(99);
    expect(mocks.unitResources).toHaveBeenCalledWith('unit-1');

    const resources = (userDetail as UserDetail).resources;
    expect(resources).toHaveLength(1);

    const resource: ResourceWithUsage = resources[0];
    expect(resource.id).toBe('res-1');
    expect(resource.used_in_units).toEqual([
      { unit_id: 'unit-1', unit_title: 'Unit One' },
    ]);
  });
});
