import { infrastructureProvider } from '../infrastructure/public';
import type {
  UnitCreationRequest,
  UnitCreationResponse,
  ContentCreatorError,
} from './models';

const CONTENT_CREATOR_BASE = '/api/v1/content-creator';

export class ContentCreatorRepo {
  private infrastructure = infrastructureProvider();

  async createUnit(
    request: UnitCreationRequest
  ): Promise<UnitCreationResponse> {
    try {
      // Build URL with optional user_id query param to associate unit ownership
      let url = `${CONTENT_CREATOR_BASE}/units`;
      if (request.ownerUserId != null) {
        const qs = new URLSearchParams({
          user_id: String(request.ownerUserId),
        });
        url = `${url}?${qs.toString()}`;
      }

      const response = await this.infrastructure.request<{
        unit_id: string;
        status: string;
        title: string;
      }>(url, {
        method: 'POST',
        body: JSON.stringify({
          topic: request.topic,
          difficulty: request.difficulty,
          target_lesson_count: request.targetLessonCount,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      });

      return {
        unitId: response.unit_id,
        status: response.status as UnitCreationResponse['status'],
        title: response.title,
      };
    } catch (error) {
      throw this.handleError(error, 'Failed to create unit');
    }
  }

  async retryUnitCreation(unitId: string): Promise<UnitCreationResponse> {
    try {
      const response = await this.infrastructure.request<{
        unit_id: string;
        status: string;
        title: string;
      }>(`${CONTENT_CREATOR_BASE}/units/${encodeURIComponent(unitId)}/retry`, {
        method: 'POST',
      });

      return {
        unitId: response.unit_id,
        status: response.status as UnitCreationResponse['status'],
        title: response.title,
      };
    } catch (error) {
      throw this.handleError(error, 'Failed to retry unit creation');
    }
  }

  async dismissUnit(unitId: string): Promise<void> {
    try {
      await this.infrastructure.request<{ message: string }>(
        `${CONTENT_CREATOR_BASE}/units/${encodeURIComponent(unitId)}`,
        {
          method: 'DELETE',
        }
      );
    } catch (error) {
      throw this.handleError(error, 'Failed to dismiss unit');
    }
  }

  private handleError(error: any, defaultMessage: string): ContentCreatorError {
    console.error('[ContentCreatorRepo]', defaultMessage, error);

    if (error && typeof error === 'object') {
      return {
        message: error.message || defaultMessage,
        code: error.code || 'CONTENT_CREATOR_ERROR',
        statusCode: error.status || error.statusCode,
        details: error.details || error,
      };
    }

    return {
      message: defaultMessage,
      code: 'CONTENT_CREATOR_ERROR',
      details: error,
    };
  }
}
