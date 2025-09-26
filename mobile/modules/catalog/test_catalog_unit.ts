/**
 * Catalog Service Unit Tests
 *
 * Tests for the catalog service layer with proper mocking.
 */

import { CatalogService } from './service';
import { CatalogRepo } from './repo';
import type { UnitCreationRequest, UnitCreationResponse } from './models';

// Mock the repo
jest.mock('./repo');

describe('CatalogService', () => {
  let service: CatalogService;
  let mockRepo: jest.Mocked<CatalogRepo>;

  beforeEach(() => {
    mockRepo = new CatalogRepo() as jest.Mocked<CatalogRepo>;
    service = new CatalogService(mockRepo);
    jest.clearAllMocks();
  });

  describe('browseUnits', () => {
    it('should return transformed units from repo', async () => {
      // Arrange
      const mockApiUnits = [
        {
          id: 'unit-1',
          title: 'Test Unit 1',
          description: 'Test Description',
          learner_level: 'beginner',
          lesson_count: 5,
          status: 'completed',
          target_lesson_count: null,
          generated_from_topic: undefined,
          creation_progress: null,
          error_message: null,
        },
      ];

      mockRepo.listUnits.mockResolvedValue(mockApiUnits);

      // Act
      const result = await service.browseUnits();

      // Assert
      expect(result).toHaveLength(1);
      expect(result[0]).toMatchObject({
        id: 'unit-1',
        title: 'Test Unit 1',
        difficulty: 'beginner',
        status: 'completed',
        difficultyLabel: 'Beginner',
      });
      expect(mockRepo.listUnits).toHaveBeenCalledWith(undefined);
    });

    it('should pass through limit and offset params', async () => {
      // Arrange
      mockRepo.listUnits.mockResolvedValue([]);
      const params = { limit: 10, offset: 20 };

      // Act
      await service.browseUnits(params);

      // Assert
      expect(mockRepo.listUnits).toHaveBeenCalledWith(params);
    });

    it('should handle repo errors gracefully', async () => {
      // Arrange
      const error = new Error('Network error');
      mockRepo.listUnits.mockRejectedValue(error);

      // Act & Assert
      await expect(service.browseUnits()).rejects.toMatchObject({
        message: 'Network error', // Original error message is preserved
        code: 'CATALOG_SERVICE_ERROR',
      });
    });
  });

  describe('getUnitDetail', () => {
    it('should return null for empty unit ID', async () => {
      // Act & Assert
      expect(await service.getUnitDetail('')).toBeNull();
      expect(await service.getUnitDetail('  ')).toBeNull();
      expect(mockRepo.getUnitDetail).not.toHaveBeenCalled();
    });

    it('should return transformed unit detail when found', async () => {
      // Arrange
      const mockApiUnit = {
        id: 'unit-1',
        title: 'Test Unit',
        description: 'Test Description',
        learner_level: 'intermediate',
        lesson_order: ['lesson-1', 'lesson-2'],
        lessons: [
          {
            id: 'lesson-1',
            title: 'Lesson 1',
            learner_level: 'intermediate',
            learning_objectives: ['Learn A'],
            key_concepts: ['Key A'],
            exercise_count: 3,
          },
        ],
        learning_objectives: ['Learn A', 'Learn B'],
        target_lesson_count: 5,
        source_material: null,
        generated_from_topic: true,
      };

      mockRepo.getUnitDetail.mockResolvedValue(mockApiUnit);

      // Act
      const result = await service.getUnitDetail('unit-1');

      // Assert
      expect(result).toMatchObject({
        id: 'unit-1',
        title: 'Test Unit',
        difficulty: 'intermediate',
        learningObjectives: ['Learn A', 'Learn B'],
      });
      expect(mockRepo.getUnitDetail).toHaveBeenCalledWith('unit-1');
    });

    it('should return null for 404 errors', async () => {
      // Arrange
      const error = { statusCode: 404, message: 'Not found' };
      mockRepo.getUnitDetail.mockRejectedValue(error);

      // Act
      const result = await service.getUnitDetail('nonexistent');

      // Assert
      expect(result).toBeNull();
    });

    it('should throw for non-404 errors', async () => {
      // Arrange
      const error = { statusCode: 500, message: 'Server error' };
      mockRepo.getUnitDetail.mockRejectedValue(error);

      // Act & Assert
      await expect(service.getUnitDetail('unit-1')).rejects.toMatchObject({
        message: 'Server error', // Original error message preserved
        code: 'CATALOG_SERVICE_ERROR',
      });
    });
  });

  describe('createUnit', () => {
    it('should create unit with valid request', async () => {
      // Arrange
      const request: UnitCreationRequest = {
        topic: 'Machine Learning',
        difficulty: 'beginner',
        targetLessonCount: 5,
      };

      const expectedResponse: UnitCreationResponse = {
        unitId: 'new-unit-id',
        status: 'in_progress',
        title: 'Machine Learning',
      };

      mockRepo.createUnit.mockResolvedValue(expectedResponse);

      // Act
      const result = await service.createUnit(request);

      // Assert
      expect(result).toEqual(expectedResponse);
      expect(mockRepo.createUnit).toHaveBeenCalledWith(request);
    });

    it('should validate topic is required', async () => {
      // Arrange
      const request: UnitCreationRequest = {
        topic: '',
        difficulty: 'beginner',
      };

      // Act & Assert
      await expect(service.createUnit(request)).rejects.toMatchObject({
        message: 'Topic is required',
        code: 'CATALOG_SERVICE_ERROR',
      });
      expect(mockRepo.createUnit).not.toHaveBeenCalled();
    });

    it('should validate difficulty level', async () => {
      // Arrange
      const request = {
        topic: 'Test Topic',
        difficulty: 'expert' as any, // Invalid difficulty
      };

      // Act & Assert
      await expect(service.createUnit(request)).rejects.toMatchObject({
        message: 'Invalid difficulty level',
        code: 'CATALOG_SERVICE_ERROR',
      });
      expect(mockRepo.createUnit).not.toHaveBeenCalled();
    });

    it('should validate target lesson count range', async () => {
      // Arrange
      const requestTooLow: UnitCreationRequest = {
        topic: 'Test Topic',
        difficulty: 'beginner',
        targetLessonCount: 0,
      };

      const requestTooHigh: UnitCreationRequest = {
        topic: 'Test Topic',
        difficulty: 'beginner',
        targetLessonCount: 25,
      };

      // Act & Assert
      await expect(service.createUnit(requestTooLow)).rejects.toMatchObject({
        message: 'Target lesson count must be between 1 and 20',
      });

      await expect(service.createUnit(requestTooHigh)).rejects.toMatchObject({
        message: 'Target lesson count must be between 1 and 20',
      });

      expect(mockRepo.createUnit).not.toHaveBeenCalled();
    });

    it('should allow null/undefined target lesson count', async () => {
      // Arrange
      const requestNull: UnitCreationRequest = {
        topic: 'Test Topic',
        difficulty: 'beginner',
        targetLessonCount: null,
      };

      const requestUndefined: UnitCreationRequest = {
        topic: 'Test Topic',
        difficulty: 'beginner',
        targetLessonCount: undefined,
      };

      const mockResponse: UnitCreationResponse = {
        unitId: 'test-id',
        status: 'in_progress',
        title: 'Test Topic',
      };

      mockRepo.createUnit.mockResolvedValue(mockResponse);

      // Act
      await service.createUnit(requestNull);
      await service.createUnit(requestUndefined);

      // Assert
      expect(mockRepo.createUnit).toHaveBeenCalledTimes(2);
    });

    it('should handle repo errors', async () => {
      // Arrange
      const request: UnitCreationRequest = {
        topic: 'Test Topic',
        difficulty: 'beginner',
      };

      const error = new Error('API Error');
      mockRepo.createUnit.mockRejectedValue(error);

      // Act & Assert
      await expect(service.createUnit(request)).rejects.toMatchObject({
        message: 'API Error', // Original error message preserved
        code: 'CATALOG_SERVICE_ERROR',
      });
    });
  });

  describe('retryUnitCreation', () => {
    it('should retry unit creation with valid unit ID', async () => {
      // Arrange
      const expectedResponse: UnitCreationResponse = {
        unitId: 'retry-unit-id',
        status: 'in_progress',
        title: 'Retried Unit',
      };

      mockRepo.retryUnitCreation.mockResolvedValue(expectedResponse);

      // Act
      const result = await service.retryUnitCreation('retry-unit-id');

      // Assert
      expect(result).toEqual(expectedResponse);
      expect(mockRepo.retryUnitCreation).toHaveBeenCalledWith('retry-unit-id');
    });

    it('should validate unit ID is required', async () => {
      // Act & Assert
      await expect(service.retryUnitCreation('')).rejects.toMatchObject({
        message: 'Unit ID is required',
        code: 'CATALOG_SERVICE_ERROR',
      });

      await expect(service.retryUnitCreation('  ')).rejects.toMatchObject({
        message: 'Unit ID is required',
        code: 'CATALOG_SERVICE_ERROR',
      });

      expect(mockRepo.retryUnitCreation).not.toHaveBeenCalled();
    });

    it('should handle repo errors', async () => {
      // Arrange
      const error = new Error('Retry failed');
      mockRepo.retryUnitCreation.mockRejectedValue(error);

      // Act & Assert
      await expect(service.retryUnitCreation('unit-id')).rejects.toMatchObject({
        message: 'Retry failed', // Original error message preserved
        code: 'CATALOG_SERVICE_ERROR',
      });
    });
  });

  describe('dismissUnit', () => {
    it('should dismiss unit with valid unit ID', async () => {
      // Arrange
      mockRepo.dismissUnit.mockResolvedValue();

      // Act
      await service.dismissUnit('dismiss-unit-id');

      // Assert
      expect(mockRepo.dismissUnit).toHaveBeenCalledWith('dismiss-unit-id');
    });

    it('should validate unit ID is required', async () => {
      // Act & Assert
      await expect(service.dismissUnit('')).rejects.toMatchObject({
        message: 'Unit ID is required',
        code: 'CATALOG_SERVICE_ERROR',
      });

      await expect(service.dismissUnit('  ')).rejects.toMatchObject({
        message: 'Unit ID is required',
        code: 'CATALOG_SERVICE_ERROR',
      });

      expect(mockRepo.dismissUnit).not.toHaveBeenCalled();
    });

    it('should handle repo errors', async () => {
      // Arrange
      const error = new Error('Dismiss failed');
      mockRepo.dismissUnit.mockRejectedValue(error);

      // Act & Assert
      await expect(service.dismissUnit('unit-id')).rejects.toMatchObject({
        message: 'Dismiss failed', // Original error message preserved
        code: 'CATALOG_SERVICE_ERROR',
      });
    });
  });

  describe('getLessonDetail', () => {
    it('should return null for empty lesson ID', async () => {
      // Act & Assert
      expect(await service.getLessonDetail('')).toBeNull();
      expect(await service.getLessonDetail('  ')).toBeNull();
      expect(mockRepo.getLessonDetail).not.toHaveBeenCalled();
    });

    it('should return null for 404 errors', async () => {
      // Arrange
      const error = { statusCode: 404, message: 'Not found' };
      mockRepo.getLessonDetail.mockRejectedValue(error);

      // Act
      const result = await service.getLessonDetail('nonexistent');

      // Assert
      expect(result).toBeNull();
    });

    it('should throw for non-404 errors', async () => {
      // Arrange
      const error = { statusCode: 500, message: 'Server error' };
      mockRepo.getLessonDetail.mockRejectedValue(error);

      // Act & Assert
      await expect(service.getLessonDetail('lesson-1')).rejects.toMatchObject({
        message: 'Server error', // Original error message preserved
        code: 'CATALOG_SERVICE_ERROR',
      });
    });
  });

  describe('browseLessons', () => {
    it('should handle empty response', async () => {
      // Arrange
      mockRepo.browseLessons.mockResolvedValue({ lessons: [], total: 0 });

      // Act
      const result = await service.browseLessons();

      // Assert
      expect(result.lessons).toHaveLength(0);
      expect(result.total).toBe(0);
    });

    it('should handle repo errors', async () => {
      // Arrange
      const error = new Error('Browse failed');
      mockRepo.browseLessons.mockRejectedValue(error);

      // Act & Assert
      await expect(service.browseLessons()).rejects.toMatchObject({
        message: 'Browse failed', // Original error message preserved
        code: 'CATALOG_SERVICE_ERROR',
      });
    });
  });

  describe('searchLessons', () => {
    it('should handle empty query', async () => {
      // Arrange
      mockRepo.searchLessons.mockResolvedValue({ lessons: [], total: 0 });

      // Act
      const _result = await service.searchLessons('');

      // Assert
      expect(mockRepo.searchLessons).toHaveBeenCalledWith({
        query: undefined, // Empty query becomes undefined
        learnerLevel: undefined,
        minDuration: undefined,
        maxDuration: undefined,
        readyOnly: undefined,
        limit: 100,
        offset: 0,
      });
    });

    it('should handle search errors', async () => {
      // Arrange
      const error = new Error('Search failed');
      mockRepo.searchLessons.mockRejectedValue(error);

      // Act & Assert
      await expect(service.searchLessons('test query')).rejects.toMatchObject({
        message: 'Search failed', // Original error message preserved
        code: 'CATALOG_SERVICE_ERROR',
      });
    });
  });

  describe('getPopularLessons', () => {
    it('should use default limit when not provided', async () => {
      // Arrange
      mockRepo.getPopularLessons.mockResolvedValue({ lessons: [], total: 0 });

      // Act
      await service.getPopularLessons();

      // Assert
      expect(mockRepo.getPopularLessons).toHaveBeenCalledWith(10);
    });

    it('should handle errors', async () => {
      // Arrange
      const error = new Error('Popular lessons failed');
      mockRepo.getPopularLessons.mockRejectedValue(error);

      // Act & Assert
      await expect(service.getPopularLessons()).rejects.toMatchObject({
        message: 'Popular lessons failed', // Original error message preserved
        code: 'CATALOG_SERVICE_ERROR',
      });
    });
  });

  describe('checkHealth', () => {
    it('should return false on repo error without throwing', async () => {
      // Arrange
      const error = new Error('Health check failed');
      mockRepo.checkHealth.mockRejectedValue(error);

      // Act
      const result = await service.checkHealth();

      // Assert
      expect(result).toBe(false);
    });

    it('should return true when repo is healthy', async () => {
      // Arrange
      mockRepo.checkHealth.mockResolvedValue(true);

      // Act
      const result = await service.checkHealth();

      // Assert
      expect(result).toBe(true);
    });
  });
});
