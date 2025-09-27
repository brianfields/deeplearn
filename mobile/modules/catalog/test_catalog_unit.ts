/**
 * Catalog Service Unit Tests
 *
 * Tests for the catalog service layer with proper mocking.
 */

import { CatalogService } from './service';
import { CatalogRepo } from './repo';
import type {
  ContentProvider,
  Unit,
  UnitDetail,
  UserUnitCollections,
} from '../content/public';
import type {
  ContentCreatorProvider,
  UnitCreationRequest,
  UnitCreationResponse,
} from '../content_creator/public';

// Mock the repo - lesson endpoints are handled directly here
jest.mock('./repo');

describe('CatalogService', () => {
  let service: CatalogService;
  let mockRepo: jest.Mocked<CatalogRepo>;
  let mockContent: jest.Mocked<ContentProvider>;
  let mockContentCreator: jest.Mocked<ContentCreatorProvider>;

  beforeEach(() => {
    mockRepo = new CatalogRepo() as jest.Mocked<CatalogRepo>;

    mockContent = {
      listUnits: jest.fn(),
      getUnitDetail: jest.fn(),
      listPersonalUnits: jest.fn(),
      listGlobalUnits: jest.fn(),
      getUserUnitCollections: jest.fn(),
      updateUnitSharing: jest.fn(),
    } as unknown as jest.Mocked<ContentProvider>;

    mockContentCreator = {
      createUnit: jest.fn(),
      retryUnitCreation: jest.fn(),
      dismissUnit: jest.fn(),
    } as unknown as jest.Mocked<ContentCreatorProvider>;

    service = new CatalogService(mockRepo, {
      content: mockContent,
      contentCreator: mockContentCreator,
    });

    jest.clearAllMocks();
  });

  describe('browseUnits', () => {
    it('returns units from content provider', async () => {
      const mockUnits: Unit[] = [
        {
          id: 'unit-1',
          title: 'Test Unit',
          description: 'Unit description',
          difficulty: 'beginner',
          lessonCount: 3,
          difficultyLabel: 'Beginner',
          status: 'completed',
          creationProgress: null,
          errorMessage: null,
          targetLessonCount: null,
          generatedFromTopic: false,
          statusLabel: 'Ready',
          isInteractive: true,
          progressMessage: 'Ready to learn',
          ownerUserId: 10,
          isGlobal: false,
          ownershipLabel: 'Personal',
          isOwnedByCurrentUser: false,
        },
      ];
      mockContent.listUnits.mockResolvedValue(mockUnits);

      const result = await service.browseUnits({ limit: 5, currentUserId: 10 });

      expect(result).toEqual(mockUnits);
      expect(mockContent.listUnits).toHaveBeenCalledWith({
        limit: 5,
        currentUserId: 10,
      });
    });

    it('wraps provider errors as catalog errors', async () => {
      mockContent.listUnits.mockRejectedValue({
        message: 'boom',
        code: 'CONTENT_ERROR',
      });

      await expect(service.browseUnits()).rejects.toMatchObject({
        message: 'boom',
        code: 'CONTENT_ERROR',
      });
    });
  });

  describe('getUnitDetail', () => {
    it('returns null when unit id is blank', async () => {
      expect(await service.getUnitDetail('')).toBeNull();
      expect(mockContent.getUnitDetail).not.toHaveBeenCalled();
    });

    it('delegates to content provider', async () => {
      const detail: UnitDetail = {
        id: 'unit-2',
        title: 'Detail',
        description: null,
        difficulty: 'intermediate',
        lessonIds: [],
        lessons: [],
        learningObjectives: null,
        targetLessonCount: null,
        sourceMaterial: null,
        generatedFromTopic: false,
        ownerUserId: 1,
        isGlobal: false,
        isOwnedByCurrentUser: true,
      };
      mockContent.getUnitDetail.mockResolvedValue(detail);

      const result = await service.getUnitDetail('unit-2', 1);

      expect(result).toEqual(detail);
      expect(mockContent.getUnitDetail).toHaveBeenCalledWith('unit-2', {
        currentUserId: 1,
      });
    });
  });

  describe('getUserUnitCollections', () => {
    it('returns collections from content provider', async () => {
      const collections: UserUnitCollections = {
        personalUnits: [],
        globalUnits: [],
      };
      mockContent.getUserUnitCollections.mockResolvedValue(collections);

      const result = await service.getUserUnitCollections(5, {
        includeGlobal: true,
      });

      expect(result).toBe(collections);
      expect(mockContent.getUserUnitCollections).toHaveBeenCalledWith(5, {
        includeGlobal: true,
      });
    });
  });

  describe('toggleUnitSharing', () => {
    it('calls content provider to update sharing', async () => {
      const updatedUnit = { id: 'unit-3' } as Unit;
      mockContent.updateUnitSharing.mockResolvedValue(updatedUnit);

      const result = await service.toggleUnitSharing('unit-3', {
        makeGlobal: true,
        actingUserId: 9,
      });

      expect(result).toBe(updatedUnit);
      expect(mockContent.updateUnitSharing).toHaveBeenCalledWith(
        'unit-3',
        { isGlobal: true, actingUserId: 9 },
        9
      );
    });
  });

  describe('createUnit', () => {
    it('validates request and calls content creator', async () => {
      const request: UnitCreationRequest = {
        topic: 'Machine Learning',
        difficulty: 'beginner',
        targetLessonCount: 3,
        shareGlobally: true,
        ownerUserId: 7,
      };
      const response: UnitCreationResponse = {
        unitId: 'new-unit',
        status: 'in_progress',
        title: 'Machine Learning',
      };
      mockContentCreator.createUnit.mockResolvedValue(response);
      mockContent.updateUnitSharing.mockResolvedValue({} as Unit);

      const result = await service.createUnit(request);

      expect(result).toBe(response);
      expect(mockContentCreator.createUnit).toHaveBeenCalledWith(request);
      expect(mockContent.updateUnitSharing).toHaveBeenCalledWith(
        'new-unit',
        { isGlobal: true, actingUserId: 7 },
        7
      );
    });

    it('rejects invalid topics', async () => {
      const request: UnitCreationRequest = {
        topic: '  ',
        difficulty: 'beginner',
      };

      await expect(service.createUnit(request)).rejects.toMatchObject({
        message: 'Topic is required',
        code: 'CATALOG_SERVICE_ERROR',
      });
      expect(mockContentCreator.createUnit).not.toHaveBeenCalled();
    });
  });

  describe('retryUnitCreation', () => {
    it('delegates to content creator', async () => {
      const response: UnitCreationResponse = {
        unitId: 'unit-4',
        status: 'in_progress',
        title: 'Retry',
      };
      mockContentCreator.retryUnitCreation.mockResolvedValue(response);

      const result = await service.retryUnitCreation('unit-4');

      expect(result).toBe(response);
      expect(mockContentCreator.retryUnitCreation).toHaveBeenCalledWith('unit-4');
    });
  });

  describe('dismissUnit', () => {
    it('delegates to content creator', async () => {
      await service.dismissUnit('unit-5');

      expect(mockContentCreator.dismissUnit).toHaveBeenCalledWith('unit-5');
    });
  });
});
