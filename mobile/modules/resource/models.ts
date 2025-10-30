import type { ResourceService } from './service';

export type ResourceType = 'file_upload' | 'url' | 'photo';

export interface Resource {
  readonly id: string;
  readonly userId: number;
  readonly resourceType: ResourceType;
  readonly filename: string | null;
  readonly sourceUrl: string | null;
  readonly extractedText: string;
  readonly extractionMetadata: Record<string, unknown>;
  readonly fileSize: number | null;
  readonly createdAt: string;
  readonly updatedAt: string;
}

export interface ResourceSummary {
  readonly id: string;
  readonly resourceType: ResourceType;
  readonly filename: string | null;
  readonly sourceUrl: string | null;
  readonly fileSize: number | null;
  readonly createdAt: string;
  readonly previewText: string;
}

export interface UploadableFile {
  readonly uri: string;
  readonly name: string;
  readonly type: string;
  readonly size?: number | null;
}

export interface CreateResourceRequest {
  readonly userId: number;
  readonly file: UploadableFile;
}

export interface PhotoResourceCreate {
  readonly userId: number;
  readonly file: UploadableFile;
}

export interface AddResourceFromURLRequest {
  readonly userId: number;
  readonly url: string;
}

export interface ResourceApiResponse {
  readonly id: string;
  readonly user_id: number;
  readonly resource_type: ResourceType;
  readonly filename: string | null;
  readonly source_url: string | null;
  readonly extracted_text: string;
  readonly extraction_metadata: Record<string, unknown>;
  readonly file_size: number | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface ResourceSummaryApiResponse {
  readonly id: string;
  readonly resource_type: ResourceType;
  readonly filename: string | null;
  readonly source_url: string | null;
  readonly file_size: number | null;
  readonly created_at: string;
  readonly preview_text: string;
}

export type ResourceServiceContract = Pick<
  ResourceService,
  | 'uploadFileResource'
  | 'uploadPhotoResource'
  | 'addResourceFromUrl'
  | 'listUserResources'
  | 'getResourceDetail'
>;
