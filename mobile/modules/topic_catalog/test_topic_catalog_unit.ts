/**
 * Topic Catalog Unit Tests
 *
 * Tests topic browsing, search, and discovery functionality.
 */

import { jest } from '@jest/globals';

import { TopicCatalogService } from './service';
import { TopicCatalogRepo } from './repo';
import { topicCatalogProvider } from './public';
import { toTopicSummaryDTO, toBrowseTopicsResponseDTO } from './models';
import type { TopicFilters } from './models';

// Mock the infrastructure module
jest.mock('../infrastructure/public', () => ({
  infrastructureProvider: () => ({
    request: jest.fn(),
    getNetworkStatus: jest.fn(() => ({ isConnected: true })),
  }),
}));

describe('Topic Catalog Module', () => {
  // Mock console methods to suppress output during tests
  const consoleWarnSpy = jest
    .spyOn(console, 'warn')
    .mockImplementation(() => {});
  const consoleErrorSpy = jest
    .spyOn(console, 'error')
    .mockImplementation(() => {});

  afterAll(() => {
    consoleWarnSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });

  describe('TopicCatalogService', () => {
    let service: TopicCatalogService;
    let mockRepo: jest.Mocked<TopicCatalogRepo>;

    beforeEach(() => {
      mockRepo = {
        browseTopics: jest.fn(),
        getTopicDetail: jest.fn(),
        searchTopics: jest.fn(),
        getPopularTopics: jest.fn(),
        getCatalogStatistics: jest.fn(),
        refreshCatalog: jest.fn(),
        checkHealth: jest.fn(),
      } as any;

      service = new TopicCatalogService(mockRepo);
    });

    describe('browseTopics', () => {
      it('should browse topics successfully', async () => {
        const mockApiResponse = {
          topics: [
            {
              id: 'topic-1',
              title: 'React Basics',
              core_concept: 'Components',
              user_level: 'beginner',
              learning_objectives: ['Learn JSX', 'Understand components'],
              key_concepts: ['JSX', 'Props', 'State'],
              component_count: 5,
            },
          ],
          total: 1,
        };

        mockRepo.browseTopics.mockResolvedValue(mockApiResponse);

        const result = await service.browseTopics();

        expect(result.topics).toHaveLength(1);
        expect(result.topics[0].title).toBe('React Basics');
        expect(result.topics[0].userLevel).toBe('beginner');
        expect(result.topics[0].estimatedDuration).toBe(15); // 5 components * 3 min
        expect(result.topics[0].isReadyForLearning).toBe(true);
        expect(result.total).toBe(1);
      });

      it('should apply client-side filters', async () => {
        const mockApiResponse = {
          topics: [
            {
              id: 'topic-1',
              title: 'React Basics',
              core_concept: 'Components',
              user_level: 'beginner',
              learning_objectives: ['Learn JSX'],
              key_concepts: ['JSX'],
              component_count: 2,
            },
            {
              id: 'topic-2',
              title: 'Advanced React',
              core_concept: 'Hooks',
              user_level: 'advanced',
              learning_objectives: ['Master hooks'],
              key_concepts: ['Hooks'],
              component_count: 10,
            },
          ],
          total: 2,
        };

        mockRepo.browseTopics.mockResolvedValue(mockApiResponse);

        const filters: TopicFilters = {
          query: 'react',
          maxDuration: 20, // Should filter out topic-2 (30 min)
        };

        const result = await service.browseTopics(filters);

        expect(result.topics).toHaveLength(1);
        expect(result.topics[0].id).toBe('topic-1');
      });
    });

    describe('getTopicDetail', () => {
      it('should get topic details successfully', async () => {
        const mockApiResponse = {
          id: 'topic-1',
          title: 'React Basics',
          core_concept: 'Components',
          user_level: 'beginner',
          learning_objectives: ['Learn JSX'],
          key_concepts: ['JSX', 'Props'],
          components: [{ id: 'comp-1' }, { id: 'comp-2' }],
          created_at: '2024-01-01T00:00:00Z',
          component_count: 2,
        };

        mockRepo.getTopicDetail.mockResolvedValue(mockApiResponse);

        const result = await service.getTopicDetail('topic-1');

        expect(result).not.toBeNull();
        expect(result!.id).toBe('topic-1');
        expect(result!.title).toBe('React Basics');
        expect(result!.components).toHaveLength(2);
        expect(result!.isReadyForLearning).toBe(true);
      });

      it('should return null for empty topic ID', async () => {
        const result = await service.getTopicDetail('');
        expect(result).toBeNull();
      });

      it('should return null for 404 errors', async () => {
        mockRepo.getTopicDetail.mockRejectedValue({ statusCode: 404 });

        const result = await service.getTopicDetail('nonexistent');
        expect(result).toBeNull();
      });
    });

    describe('searchTopics', () => {
      it('should search topics successfully', async () => {
        const mockApiResponse = {
          topics: [
            {
              id: 'topic-1',
              title: 'React Basics',
              core_concept: 'Components',
              user_level: 'beginner',
              learning_objectives: ['Learn React'],
              key_concepts: ['JSX'],
              component_count: 3,
            },
          ],
          total: 1,
        };

        mockRepo.searchTopics.mockResolvedValue(mockApiResponse);

        const result = await service.searchTopics('react');

        expect(result.topics).toHaveLength(1);
        expect(result.topics[0].title).toBe('React Basics');
        expect(mockRepo.searchTopics).toHaveBeenCalledWith({
          query: 'react',
          limit: 100,
          offset: 0,
        });
      });
    });

    describe('checkHealth', () => {
      it('should return health status', async () => {
        mockRepo.checkHealth.mockResolvedValue(true);

        const result = await service.checkHealth();
        expect(result).toBe(true);
      });

      it('should handle health check errors', async () => {
        mockRepo.checkHealth.mockRejectedValue(new Error('Network error'));

        const result = await service.checkHealth();
        expect(result).toBe(false);
      });
    });
  });

  describe('DTO Converters', () => {
    describe('toTopicSummaryDTO', () => {
      it('should convert API response to DTO correctly', () => {
        const apiTopic = {
          id: 'topic-1',
          title: 'React Basics',
          core_concept: 'Components',
          user_level: 'beginner',
          learning_objectives: ['Learn JSX', 'Understand props'],
          key_concepts: ['JSX', 'Props', 'State', 'Events'],
          component_count: 4,
        };

        const dto = toTopicSummaryDTO(apiTopic);

        expect(dto.id).toBe('topic-1');
        expect(dto.title).toBe('React Basics');
        expect(dto.coreConcept).toBe('Components');
        expect(dto.userLevel).toBe('beginner');
        expect(dto.estimatedDuration).toBe(12); // 4 components * 3 min
        expect(dto.isReadyForLearning).toBe(true);
        expect(dto.difficultyLevel).toBe('Beginner');
        expect(dto.durationDisplay).toBe('12 min');
        expect(dto.readinessStatus).toBe('Ready');
        expect(dto.tags).toEqual(['JSX', 'Props', 'State']); // First 3 key concepts
      });

      it('should handle topics with no components', () => {
        const apiTopic = {
          id: 'topic-1',
          title: 'Draft Topic',
          core_concept: 'Test',
          user_level: 'beginner',
          learning_objectives: [],
          key_concepts: [],
          component_count: 0,
        };

        const dto = toTopicSummaryDTO(apiTopic);

        expect(dto.estimatedDuration).toBe(5); // Minimum 5 minutes
        expect(dto.isReadyForLearning).toBe(false);
        expect(dto.readinessStatus).toBe('Draft');
      });
    });

    describe('toBrowseTopicsResponseDTO', () => {
      it('should convert API response with pagination', () => {
        const apiResponse = {
          topics: [
            {
              id: 'topic-1',
              title: 'Test Topic',
              core_concept: 'Test',
              user_level: 'beginner',
              learning_objectives: [],
              key_concepts: [],
              component_count: 1,
            },
          ],
          total: 50,
        };

        const filters = { userLevel: 'beginner' as const };
        const pagination = { limit: 10, offset: 0 };

        const dto = toBrowseTopicsResponseDTO(apiResponse, filters, pagination);

        expect(dto.topics).toHaveLength(1);
        expect(dto.total).toBe(50);
        expect(dto.filters).toEqual(filters);
        expect(dto.pagination.hasMore).toBe(true); // 0 + 10 < 50
      });
    });
  });

  describe('Public Interface', () => {
    it('should provide topic catalog provider', () => {
      const provider = topicCatalogProvider();

      expect(provider).toHaveProperty('getTopicDetail');
      expect(provider).toHaveProperty('browseTopics');
      expect(provider).toHaveProperty('searchTopics');
      expect(provider).toHaveProperty('getPopularTopics');
      expect(provider).toHaveProperty('getCatalogStatistics');
      expect(provider).toHaveProperty('refreshCatalog');
      expect(provider).toHaveProperty('checkHealth');
    });

    it('should return consistent service behavior', () => {
      const provider1 = topicCatalogProvider();
      const provider2 = topicCatalogProvider();

      // Should have the same methods (service is singleton even if provider object is new)
      expect(typeof provider1.getTopicDetail).toBe('function');
      expect(typeof provider2.getTopicDetail).toBe('function');
      expect(provider1.getTopicDetail.name).toBe(provider2.getTopicDetail.name);
    });
  });
});
