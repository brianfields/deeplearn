/**
 * Units Module - Unit Tests
 *
 * Tests for UnitsService behavior and DTO mapping.
 */

import { UnitsService } from './service';
import { toUnitDTO, toUnitDetailDTO } from './models';

// Mock the repo to avoid HTTP calls in tests
const mockRepo = {
  list: jest.fn(),
  detail: jest.fn(),
};

const service = new UnitsService(mockRepo as any);

describe('UnitsService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('list', () => {
    it('maps API units to DTOs', async () => {
      mockRepo.list.mockResolvedValue([
        {
          id: 'u1',
          title: 'Unit 1',
          description: 'Description',
          difficulty: 'beginner',
          lesson_count: 5,
        },
      ]);

      const result = await service.list();

      expect(result).toHaveLength(1);
      expect(result[0]).toEqual({
        id: 'u1',
        title: 'Unit 1',
        description: 'Description',
        difficulty: 'beginner',
        lessonCount: 5,
        difficultyLabel: 'Beginner',
      });
    });
  });

  describe('detail', () => {
    it('maps API unit detail to DTO', async () => {
      mockRepo.detail.mockResolvedValue({
        id: 'u1',
        title: 'Unit 1',
        description: 'Description',
        difficulty: 'beginner',
        lesson_order: ['l1', 'l2'],
        lessons: [
          {
            id: 'l1',
            title: 'Lesson 1',
            core_concept: 'Concept',
            user_level: 'beginner',
            learning_objectives: ['obj1'],
            key_concepts: ['key1'],
            exercise_count: 3,
          },
        ],
      });

      const result = await service.detail('u1');

      expect(result?.id).toBe('u1');
      expect(result?.lessonIds).toEqual(['l1', 'l2']);
      expect(result?.lessons).toHaveLength(1);
    });

    it('returns null for invalid unit ID', async () => {
      const result = await service.detail('');
      expect(result).toBeNull();
    });
  });

  describe('progress', () => {
    it('calculates progress correctly', async () => {
      const unitDetail = {
        id: 'u1',
        title: 'Unit 1',
        description: 'Description',
        difficulty: 'beginner' as const,
        lessonIds: ['l1', 'l2'],
        lessons: [
          {
            id: 'l1',
            title: 'Lesson 1',
            coreConcept: 'Concept',
            userLevel: 'beginner' as const,
            learningObjectives: ['obj1'],
            keyConcepts: ['key1'],
            componentCount: 3,
            estimatedDuration: 9,
            isReadyForLearning: true,
            difficultyLevel: 'Beginner',
            durationDisplay: '9 min',
            readinessStatus: 'Ready',
            tags: ['key1'],
          },
          {
            id: 'l2',
            title: 'Lesson 2',
            coreConcept: 'Concept 2',
            userLevel: 'beginner' as const,
            learningObjectives: ['obj2'],
            keyConcepts: ['key2'],
            componentCount: 0,
            estimatedDuration: 5,
            isReadyForLearning: false,
            difficultyLevel: 'Beginner',
            durationDisplay: '5 min',
            readinessStatus: 'Draft',
            tags: ['key2'],
          },
        ],
      };

      const progress = await service.progress(unitDetail);

      expect(progress.unitId).toBe('u1');
      expect(progress.totalLessons).toBe(2);
      expect(progress.completedLessons).toBe(1); // Only first lesson is ready
      expect(progress.progressPercentage).toBe(50);
    });
  });
});

describe('DTO conversion helpers', () => {
  describe('toUnitDTO', () => {
    it('converts API unit to DTO', () => {
      const api = {
        id: 'u1',
        title: 'Unit 1',
        description: 'Description',
        difficulty: 'intermediate',
        lesson_count: 10,
      };

      const dto = toUnitDTO(api);

      expect(dto.id).toBe('u1');
      expect(dto.difficulty).toBe('intermediate');
      expect(dto.difficultyLabel).toBe('Intermediate');
      expect(dto.lessonCount).toBe(10);
    });
  });

  describe('toUnitDetailDTO', () => {
    it('converts API unit detail to DTO', () => {
      const api = {
        id: 'u1',
        title: 'Unit 1',
        description: 'Description',
        difficulty: 'advanced',
        lesson_order: ['l1', 'l2'],
        lessons: [
          {
            id: 'l1',
            title: 'Lesson 1',
            core_concept: 'Concept',
            user_level: 'beginner',
            learning_objectives: ['obj1'],
            key_concepts: ['key1'],
            exercise_count: 5,
          },
        ],
      };

      const dto = toUnitDetailDTO(api);

      expect(dto.id).toBe('u1');
      expect(dto.difficulty).toBe('advanced');
      expect(dto.lessonIds).toEqual(['l1', 'l2']);
      expect(dto.lessons[0].id).toBe('l1');
    });
  });
});
