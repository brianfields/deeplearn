import { infrastructureProvider } from '../infrastructure/public';
import type {
  AddResourceFromURLRequest,
  CreateResourceRequest,
  ResourceApiResponse,
  ResourceSummaryApiResponse,
} from './models';

const RESOURCE_BASE = '/api/v1/resources';

export class ResourceRepo {
  private infrastructure = infrastructureProvider();

  async uploadFileResource(
    request: CreateResourceRequest
  ): Promise<ResourceApiResponse> {
    const formData = new FormData();
    formData.append('user_id', String(request.userId));
    formData.append('file', {
      uri: request.file.uri,
      name: request.file.name,
      type: request.file.type,
    } as any);

    return this.infrastructure.request<ResourceApiResponse>(
      `${RESOURCE_BASE}/upload`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        body: formData,
      }
    );
  }

  async addResourceFromUrl(
    request: AddResourceFromURLRequest
  ): Promise<ResourceApiResponse> {
    return this.infrastructure.request<ResourceApiResponse>(
      `${RESOURCE_BASE}/from-url`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: request.userId,
          url: request.url,
        }),
      }
    );
  }

  async listUserResources(userId: number): Promise<ResourceSummaryApiResponse[]> {
    const query = new URLSearchParams({ user_id: String(userId) });
    return this.infrastructure.request<ResourceSummaryApiResponse[]>(
      `${RESOURCE_BASE}?${query.toString()}`,
      {
        method: 'GET',
      }
    );
  }

  async getResource(resourceId: string): Promise<ResourceApiResponse> {
    return this.infrastructure.request<ResourceApiResponse>(
      `${RESOURCE_BASE}/${resourceId}`,
      {
        method: 'GET',
      }
    );
  }
}
