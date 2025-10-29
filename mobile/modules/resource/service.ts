import { ResourceRepo } from './repo';
import type {
  AddResourceFromURLRequest,
  CreateResourceRequest,
  Resource,
  ResourceApiResponse,
  ResourceSummary,
  ResourceSummaryApiResponse,
} from './models';

function toResource(dto: ResourceApiResponse): Resource {
  return {
    id: dto.id,
    userId: dto.user_id,
    resourceType: dto.resource_type,
    filename: dto.filename,
    sourceUrl: dto.source_url,
    extractedText: dto.extracted_text,
    extractionMetadata: dto.extraction_metadata ?? {},
    fileSize: dto.file_size ?? null,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

function toResourceSummary(dto: ResourceSummaryApiResponse): ResourceSummary {
  return {
    id: dto.id,
    resourceType: dto.resource_type,
    filename: dto.filename,
    sourceUrl: dto.source_url,
    fileSize: dto.file_size ?? null,
    createdAt: dto.created_at,
    previewText: dto.preview_text ?? '',
  };
}

function normalizeUrl(url: string): string {
  const trimmed = url.trim();
  const parsed = new URL(trimmed);
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error('Only http and https URLs are supported');
  }
  return parsed.toString();
}

export class ResourceService {
  constructor(private repo: ResourceRepo = new ResourceRepo()) {}

  async uploadFileResource(request: CreateResourceRequest): Promise<Resource> {
    if (!request.file?.uri || !request.file.name || !request.file.type) {
      throw new Error('A valid file selection is required');
    }
    if (!Number.isFinite(request.userId) || request.userId <= 0) {
      throw new Error('A valid user is required');
    }
    const response = await this.repo.uploadFileResource(request);
    return toResource(response);
  }

  async addResourceFromUrl(
    request: AddResourceFromURLRequest
  ): Promise<Resource> {
    if (!Number.isFinite(request.userId) || request.userId <= 0) {
      throw new Error('A valid user is required');
    }
    const normalizedUrl = normalizeUrl(request.url);
    const response = await this.repo.addResourceFromUrl({
      ...request,
      url: normalizedUrl,
    });
    return toResource(response);
  }

  async listUserResources(userId: number): Promise<ResourceSummary[]> {
    if (!Number.isFinite(userId) || userId <= 0) {
      throw new Error('A valid user is required');
    }
    const response = await this.repo.listUserResources(userId);
    return response.map(toResourceSummary);
  }

  async getResourceDetail(resourceId: string): Promise<Resource> {
    if (!resourceId?.trim()) {
      throw new Error('Resource id is required');
    }
    const response = await this.repo.getResource(resourceId);
    return toResource(response);
  }
}
