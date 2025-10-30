declare module 'expo-image-picker' {
  export interface ImagePickerAsset {
    uri: string;
    width?: number;
    height?: number;
    type?: string | null;
    mimeType?: string | null;
    fileName?: string | null;
    fileSize?: number | null;
    duration?: number | null;
    exif?: Record<string, unknown> | null;
    base64?: string | null;
  }

  export interface ImagePickerResult {
    canceled: boolean;
    assets?: ImagePickerAsset[];
  }

  export interface PermissionResponse {
    status: 'undetermined' | 'granted' | 'denied';
    granted: boolean;
    canAskAgain: boolean;
    expires: string | number;
  }

  export const MediaTypeOptions: {
    readonly All: 'All';
    readonly Images: 'Images';
    readonly Videos: 'Videos';
    readonly AllRestricted: 'AllRestricted';
  };

  export type MediaTypeValue =
    (typeof MediaTypeOptions)[keyof typeof MediaTypeOptions];

  export interface ImagePickerOptions {
    mediaTypes?: MediaTypeValue;
    allowsEditing?: boolean;
    base64?: boolean;
    quality?: number;
    exif?: boolean;
    aspect?: [number, number];
  }

  export function requestCameraPermissionsAsync(): Promise<PermissionResponse>;
  export function requestMediaLibraryPermissionsAsync(): Promise<PermissionResponse>;
  export function launchCameraAsync(
    options?: ImagePickerOptions
  ): Promise<ImagePickerResult>;
  export function launchImageLibraryAsync(
    options?: ImagePickerOptions
  ): Promise<ImagePickerResult>;
}
