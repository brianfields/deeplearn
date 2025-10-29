import { ResourceService } from './service';
import type { ResourceRepo } from './repo';
import type {
  AddResourceFromURLRequest,
  CreateResourceRequest,
} from './models';

describe('ResourceService', () => {
  const sampleResourceResponse = {
    id: '1234',
    user_id: 42,
    resource_type: 'file_upload' as const,
    filename: 'notes.txt',
    source_url: null,
    extracted_text: 'Hello world',
    extraction_metadata: { source: 'file_upload' },
    file_size: 1024,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  let repo: jest.Mocked<ResourceRepo>;
  let service: ResourceService;

  beforeEach(() => {
    repo = {
      uploadFileResource: jest.fn().mockResolvedValue(sampleResourceResponse),
      addResourceFromUrl: jest.fn().mockResolvedValue({
        ...sampleResourceResponse,
        resource_type: 'url',
        source_url: 'https://example.com',
      }),
      listUserResources: jest.fn().mockResolvedValue([
        {
          id: 'abc',
          resource_type: 'url',
          filename: null,
          source_url: 'https://example.com',
          file_size: null,
          created_at: '2024-01-02T00:00:00Z',
          preview_text: 'Preview',
        },
      ]),
      getResource: jest.fn().mockResolvedValue(sampleResourceResponse),
    } as unknown as jest.Mocked<ResourceRepo>;
    service = new ResourceService(repo);
  });

  it('maps uploaded resources to DTOs', async () => {
    const request: CreateResourceRequest = {
      userId: 42,
      file: {
        uri: 'file:///path/to/file.txt',
        name: 'notes.txt',
        type: 'text/plain',
      },
    };

    const result = await service.uploadFileResource(request);
    expect(repo.uploadFileResource).toHaveBeenCalledWith(request);
    expect(result).toEqual({
      id: '1234',
      userId: 42,
      resourceType: 'file_upload',
      filename: 'notes.txt',
      sourceUrl: null,
      extractedText: 'Hello world',
      extractionMetadata: { source: 'file_upload' },
      fileSize: 1024,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    });
  });

  it('normalizes URL inputs before delegating', async () => {
    const request: AddResourceFromURLRequest = {
      userId: 42,
      url: ' https://Example.com/resources ',
    };

    await service.addResourceFromUrl(request);
    expect(repo.addResourceFromUrl).toHaveBeenCalledWith({
      userId: 42,
      url: 'https://example.com/resources',
    });
  });

  it('throws when listing resources without a valid user', async () => {
    await expect(service.listUserResources(0)).rejects.toThrow(
      'A valid user is required'
    );
  });

  it('returns resource summaries from repo responses', async () => {
    const summaries = await service.listUserResources(42);
    expect(summaries).toEqual([
      {
        id: 'abc',
        resourceType: 'url',
        filename: null,
        sourceUrl: 'https://example.com',
        fileSize: null,
        createdAt: '2024-01-02T00:00:00Z',
        previewText: 'Preview',
      },
    ]);
  });

  it('validates resource id when fetching details', async () => {
    await expect(service.getResourceDetail('')).rejects.toThrow(
      'Resource id is required'
    );
    await expect(service.getResourceDetail('1234')).resolves.toMatchObject({
      id: '1234',
    });
  });
});
