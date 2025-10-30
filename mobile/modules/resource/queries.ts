import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { resourceProvider } from './public';
import type {
  AddResourceFromURLRequest,
  CreateResourceRequest,
  PhotoResourceCreate,
  Resource,
} from './models';

const resource = resourceProvider();

export const resourceKeys = {
  all: ['resources'] as const,
  userList: (userId: number) => ['resources', 'user', userId] as const,
  detail: (resourceId: string) => ['resources', 'detail', resourceId] as const,
};

export function useUserResources(
  userId: number | null | undefined,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: resourceKeys.userList(userId ?? 0),
    queryFn: () => resource.listUserResources(userId as number),
    enabled: (options?.enabled ?? true) && !!userId,
  });
}

export function useResourceDetail(resourceId: string | null | undefined) {
  return useQuery({
    queryKey: resourceKeys.detail(resourceId ?? ''),
    queryFn: () => resource.getResourceDetail(resourceId as string),
    enabled: !!resourceId,
  });
}

export function useUploadResource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateResourceRequest) =>
      resource.uploadFileResource(payload),
    onSuccess: (result: Resource) => {
      queryClient.invalidateQueries({
        queryKey: resourceKeys.userList(result.userId),
      });
      queryClient.setQueryData(resourceKeys.detail(result.id), result);
    },
  });
}

export function useAddResourceFromURL() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AddResourceFromURLRequest) =>
      resource.addResourceFromUrl(payload),
    onSuccess: (result: Resource) => {
      queryClient.invalidateQueries({
        queryKey: resourceKeys.userList(result.userId),
      });
      queryClient.setQueryData(resourceKeys.detail(result.id), result);
    },
  });
}

export function useUploadPhotoResource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PhotoResourceCreate) =>
      resource.uploadPhotoResource(payload),
    onSuccess: (result: Resource) => {
      queryClient.invalidateQueries({
        queryKey: resourceKeys.userList(result.userId),
      });
      queryClient.setQueryData(resourceKeys.detail(result.id), result);
    },
  });
}
