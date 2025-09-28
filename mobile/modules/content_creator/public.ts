import { ContentCreatorService } from './service';
import { ContentCreatorRepo } from './repo';
import type { UnitCreationRequest, UnitCreationResponse } from './models';

export interface ContentCreatorProvider {
  createUnit(request: UnitCreationRequest): Promise<UnitCreationResponse>;
  retryUnitCreation(unitId: string): Promise<UnitCreationResponse>;
  dismissUnit(unitId: string): Promise<void>;
}

let serviceInstance: ContentCreatorService | null = null;

function getServiceInstance(): ContentCreatorService {
  if (!serviceInstance) {
    const repo = new ContentCreatorRepo();
    serviceInstance = new ContentCreatorService(repo);
  }
  return serviceInstance;
}

export function contentCreatorProvider(): ContentCreatorProvider {
  const service = getServiceInstance();
  return {
    createUnit: service.createUnit.bind(service),
    retryUnitCreation: service.retryUnitCreation.bind(service),
    dismissUnit: service.dismissUnit.bind(service),
  };
}

export type {
  UnitCreationRequest,
  UnitCreationResponse,
  ContentCreatorError,
} from './models';
