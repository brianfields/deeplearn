import { ResourceService } from './service';
import type { ResourceServiceContract } from './models';

export interface ResourceProvider extends ResourceServiceContract {
  uploadFileResource: ResourceService['uploadFileResource'];
  addResourceFromUrl: ResourceService['addResourceFromUrl'];
  listUserResources: ResourceService['listUserResources'];
  getResourceDetail: ResourceService['getResourceDetail'];
}

let serviceInstance: ResourceService | null = null;

function getService(): ResourceService {
  if (!serviceInstance) {
    serviceInstance = new ResourceService();
  }
  return serviceInstance;
}

export function resourceProvider(): ResourceProvider {
  const service = getService();
  return {
    uploadFileResource: service.uploadFileResource.bind(service),
    addResourceFromUrl: service.addResourceFromUrl.bind(service),
    listUserResources: service.listUserResources.bind(service),
    getResourceDetail: service.getResourceDetail.bind(service),
  };
}

export type { Resource, ResourceSummary, ResourceType } from './models';
export type {
  CreateResourceRequest,
  AddResourceFromURLRequest,
} from './models';
