import { ContentCreatorRepo } from './repo';
import type {
  UnitCreationRequest,
  UnitCreationResponse,
  ContentCreatorError,
} from './models';

export class ContentCreatorService {
  constructor(private repo: ContentCreatorRepo) {}

  async createUnit(
    request: UnitCreationRequest
  ): Promise<UnitCreationResponse> {
    try {
      return await this.repo.createUnit(request);
    } catch (error) {
      throw this.handleError(error, 'Failed to create unit');
    }
  }

  async retryUnitCreation(unitId: string): Promise<UnitCreationResponse> {
    if (!unitId?.trim()) {
      throw this.handleError(
        new Error('Unit ID is required'),
        'Unit ID is required'
      );
    }

    try {
      return await this.repo.retryUnitCreation(unitId);
    } catch (error) {
      throw this.handleError(error, 'Failed to retry unit creation');
    }
  }

  async dismissUnit(unitId: string): Promise<void> {
    if (!unitId?.trim()) {
      throw this.handleError(
        new Error('Unit ID is required'),
        'Unit ID is required'
      );
    }

    try {
      await this.repo.dismissUnit(unitId);
    } catch (error) {
      throw this.handleError(error, 'Failed to dismiss unit');
    }
  }

  private handleError(error: any, defaultMessage: string): ContentCreatorError {
    if (error && typeof error === 'object' && 'code' in error) {
      return error as ContentCreatorError;
    }

    return {
      message: (error as Error)?.message || defaultMessage,
      code: 'CONTENT_CREATOR_SERVICE_ERROR',
      details: error,
    };
  }
}
