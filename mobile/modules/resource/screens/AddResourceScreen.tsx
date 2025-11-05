import React, { useCallback, useState, useMemo } from 'react';
import * as ImagePicker from 'expo-image-picker';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import DocumentPicker, {
  types as DocumentPickerTypes,
} from 'react-native-document-picker';
import { useAuth } from '../../user/public';
import {
  useUserResources,
  useUploadResource,
  useUploadPhotoResource,
  useAddResourceFromURL,
} from '../queries';
import type { ResourceSummary } from '../models';
import { ResourcePicker } from '../components/ResourcePicker';
import type { LearningStackParamList } from '../../../types';
import { useLearningCoachSession } from '../../learning_conversations/queries';
import { uiSystemProvider } from '../../ui_system/public';

const uiSystem = uiSystemProvider();
const theme = uiSystem.getCurrentTheme();

const URL_REGEX = /^(https?:\/\/).+/i;

export type AddResourceScreenParams = {
  readonly attachToConversation?: boolean;
  readonly conversationId?: string | null;
};

type ScreenProps = NativeStackScreenProps<
  LearningStackParamList,
  'AddResource'
>;

export function AddResourceScreen({
  navigation,
  route,
}: ScreenProps): React.ReactElement {
  const { user } = useAuth();
  const userId = user?.id ?? null;
  const [url, setUrl] = useState('');
  const [urlError, setUrlError] = useState<string | null>(null);
  const [photoStatus, setPhotoStatus] = useState<string | null>(null);
  const [activePhotoAction, setActivePhotoAction] = useState<
    'camera' | 'library' | null
  >(null);
  const uploadMutation = useUploadResource();
  const photoMutation = useUploadPhotoResource();
  const urlMutation = useAddResourceFromURL();
  const isPhotoProcessing = photoMutation.isPending;
  const isBusy =
    uploadMutation.isPending || urlMutation.isPending || isPhotoProcessing;
  const resourcesQuery = useUserResources(userId, { enabled: !!userId });
  const attachToConversation = route.params?.attachToConversation ?? false;

  // Get conversation ID from navigation state to fetch shared resources
  const conversationId = route.params?.conversationId ?? null;
  const sessionQuery = useLearningCoachSession(
    attachToConversation ? conversationId : null
  );
  const sharedResourceIds = useMemo(
    () => new Set(sessionQuery.data?.resources?.map(r => r.id) ?? []),
    [sessionQuery.data?.resources]
  );

  const handleResourceAttached = useCallback(
    (resourceId: string) => {
      if (!attachToConversation || !conversationId) {
        return;
      }
      // Update the LearningCoach screen params and go back to it
      navigation.navigate({
        name: 'LearningCoach',
        params: {
          conversationId: conversationId,
          attachResourceId: resourceId,
        },
        merge: true, // Merge with existing params instead of replacing
      } as any);
    },
    [attachToConversation, conversationId, navigation]
  );

  const handleFileUpload = useCallback(async () => {
    if (!userId) {
      Alert.alert('Sign in required', 'Please sign in to upload resources.');
      return;
    }
    try {
      const file = await DocumentPicker.pickSingle({
        presentationStyle: 'fullScreen',
        type: [
          DocumentPickerTypes.pdf,
          DocumentPickerTypes.plainText,
          DocumentPickerTypes.audio,
          DocumentPickerTypes.images,
          DocumentPickerTypes.allFiles,
        ],
      });
      if (!file?.uri) {
        throw new Error('File selection failed.');
      }
      uploadMutation.mutate(
        {
          userId,
          file: {
            uri: file.fileCopyUri ?? file.uri,
            name: file.name ?? 'uploaded-resource',
            type: file.type ?? 'application/octet-stream',
            size: file.size ?? null,
          },
        },
        {
          onSuccess: result => {
            if (attachToConversation) {
              handleResourceAttached(result.id);
            }
            Alert.alert(
              'Upload complete',
              attachToConversation
                ? 'Sharing this with your learning coach now.'
                : 'Your resource has been uploaded.'
            );
            navigation.goBack();
          },
          onError: (error: unknown) => {
            const message =
              error instanceof Error
                ? error.message
                : 'Failed to upload resource.';
            Alert.alert('Upload failed', message);
          },
        }
      );
    } catch (error: unknown) {
      if (DocumentPicker.isCancel(error)) {
        return;
      }
      const message =
        error instanceof Error
          ? error.message
          : 'Unable to pick the selected file.';
      Alert.alert('File selection error', message);
    }
  }, [
    navigation,
    uploadMutation,
    userId,
    attachToConversation,
    handleResourceAttached,
  ]);

  const handleUrlSubmit = useCallback(() => {
    if (!userId) {
      Alert.alert('Sign in required', 'Please sign in to add resources.');
      return;
    }
    if (!url.trim()) {
      setUrlError('Please enter a URL.');
      return;
    }
    if (!URL_REGEX.test(url.trim())) {
      setUrlError('Enter a valid http or https URL.');
      return;
    }
    setUrlError(null);
    urlMutation.mutate(
      { userId, url },
      {
        onSuccess: result => {
          if (attachToConversation) {
            handleResourceAttached(result.id);
          }
          Alert.alert(
            'Resource added',
            attachToConversation
              ? 'Sending this link to your learning coach.'
              : 'The URL has been saved as a resource.'
          );
          navigation.goBack();
        },
        onError: (error: unknown) => {
          const message =
            error instanceof Error
              ? error.message
              : 'Failed to add URL resource.';
          Alert.alert('Unable to add resource', message);
        },
      }
    );
  }, [
    navigation,
    url,
    urlMutation,
    userId,
    attachToConversation,
    handleResourceAttached,
  ]);

  const handleSelectResource = useCallback(
    (resource: ResourceSummary) => {
      if (attachToConversation) {
        // Check if resource is already shared
        if (sharedResourceIds.has(resource.id)) {
          // Prompt to unshare
          Alert.alert(
            'Resource already shared',
            `Would you like to unshare "${resource.filename || resource.sourceUrl || 'this resource'}"?`,
            [
              { text: 'Cancel', style: 'cancel' },
              {
                text: 'Unshare',
                style: 'destructive',
                onPress: () => {
                  // TODO: Implement unshare functionality
                  Alert.alert(
                    'Coming soon',
                    'Unsharing resources will be available soon.'
                  );
                },
              },
            ]
          );
          return;
        }

        // Attach the resource
        handleResourceAttached(resource.id);
        Alert.alert(
          'Resource selected',
          'Sharing this with your learning coach now.'
        );
        // Don't call goBack - handleResourceAttached already navigates back
        return;
      }
      // When not attaching to conversation, just go back
      // (ResourceDetail is not available in LearningStack)
      navigation.goBack();
    },
    [
      attachToConversation,
      handleResourceAttached,
      navigation,
      sharedResourceIds,
    ]
  );

  const handlePhotoFlow = useCallback(
    async (source: 'camera' | 'library') => {
      // TODO: Future - support selecting multiple photos at once
      if (photoMutation.isPending) {
        return;
      }
      if (!userId) {
        Alert.alert('Sign in required', 'Please sign in to upload photos.');
        return;
      }
      try {
        const permission =
          source === 'camera'
            ? await ImagePicker.requestCameraPermissionsAsync()
            : await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!permission.granted) {
          Alert.alert(
            source === 'camera'
              ? 'Camera access needed'
              : 'Photo access needed',
            'Please enable permissions in Settings to share photos with your coach.'
          );
          return;
        }

        const pickerResult =
          source === 'camera'
            ? await ImagePicker.launchCameraAsync({
                mediaTypes: ImagePicker.MediaTypeOptions.Images,
                quality: 1,
              })
            : await ImagePicker.launchImageLibraryAsync({
                mediaTypes: ImagePicker.MediaTypeOptions.Images,
                quality: 1,
              });

        if (pickerResult.canceled) {
          return;
        }

        const asset = pickerResult.assets?.[0];
        if (!asset?.uri) {
          Alert.alert(
            'Photo unavailable',
            'We were unable to access the selected photo.'
          );
          return;
        }

        const extension = asset.mimeType?.split('/')[1] ?? 'jpg';
        const generatedName = `photo-${Date.now()}.${extension}`;
        const name = asset.fileName ?? generatedName;
        const type = asset.mimeType ?? 'image/jpeg';

        setActivePhotoAction(source);
        setPhotoStatus('Uploading and analyzing your photo...');

        photoMutation.mutate(
          {
            userId,
            file: {
              uri: asset.uri,
              name,
              type,
              size: asset.fileSize ?? null,
            },
          },
          {
            onSuccess: result => {
              if (attachToConversation) {
                handleResourceAttached(result.id);
              }
              Alert.alert(
                'Photo shared',
                attachToConversation
                  ? "I've received your photo. Let me analyze it for you."
                  : 'Your photo has been uploaded as a resource.'
              );
              navigation.goBack();
            },
            onError: (error: unknown) => {
              const message =
                error instanceof Error
                  ? error.message
                  : 'Failed to upload your photo.';
              Alert.alert('Upload failed', message);
            },
            onSettled: () => {
              setPhotoStatus(null);
              setActivePhotoAction(null);
            },
          }
        );
      } catch (error: unknown) {
        setPhotoStatus(null);
        setActivePhotoAction(null);
        const message =
          error instanceof Error
            ? error.message
            : 'Unable to process the selected photo.';
        Alert.alert('Photo error', message);
      }
    },
    [
      attachToConversation,
      handleResourceAttached,
      navigation,
      photoMutation,
      userId,
    ]
  );

  const handleTakePhoto = useCallback(() => {
    void handlePhotoFlow('camera');
  }, [handlePhotoFlow]);

  const handleChoosePhoto = useCallback(() => {
    void handlePhotoFlow('library');
  }, [handlePhotoFlow]);

  const handleClose = useCallback(() => {
    if (isBusy) {
      Alert.alert(
        'Please wait',
        'Your upload is still processing. Stay on this screen until it finishes.'
      );
      return;
    }
    // Modal screens should always just dismiss back to the screen that opened them
    navigation.goBack();
  }, [isBusy, navigation]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Pressable
          onPress={handleClose}
          disabled={isBusy}
          style={({ pressed }) => [
            styles.closeButton,
            { opacity: isBusy ? 0.4 : pressed ? 0.6 : 1 },
          ]}
        >
          <Text style={styles.closeButtonText}>✕</Text>
        </Pressable>
        <Text style={styles.headerTitle}>Add Resource</Text>
        <View style={styles.headerSpacer} />
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.heading}>Add a new resource</Text>
        <Text style={styles.description}>
          Provide the learning coach with additional materials. Upload files,
          paste URLs, or reuse something you have already shared.
        </Text>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Upload a file</Text>
          <Pressable
            style={styles.primaryButton}
            onPress={handleFileUpload}
            disabled={isBusy}
          >
            {uploadMutation.isPending ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.primaryButtonText}>Choose file</Text>
            )}
          </Pressable>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Paste a URL</Text>
          <TextInput
            value={url}
            onChangeText={text => {
              setUrl(text);
              if (urlError) {
                setUrlError(null);
              }
            }}
            placeholder="https://example.com/article"
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            style={styles.input}
          />
          {urlError ? <Text style={styles.errorText}>{urlError}</Text> : null}
          <Pressable
            style={styles.secondaryButton}
            onPress={handleUrlSubmit}
            disabled={isBusy}
          >
            {urlMutation.isPending ? (
              <ActivityIndicator color="#1f2937" />
            ) : (
              <Text style={styles.secondaryButtonText}>Save URL</Text>
            )}
          </Pressable>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Choose a previous resource</Text>
          <ResourcePicker
            resources={resourcesQuery.data ?? []}
            onSelect={handleSelectResource}
            isLoading={resourcesQuery.isLoading}
            sharedResourceIds={sharedResourceIds}
          />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Add a photo</Text>
          <Pressable
            style={styles.primaryButton}
            onPress={handleTakePhoto}
            disabled={isPhotoProcessing}
          >
            {photoMutation.isPending && activePhotoAction === 'camera' ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.primaryButtonText}>Take a photo</Text>
            )}
          </Pressable>
          <Pressable
            style={[styles.secondaryButton, styles.photoLibraryButton]}
            onPress={handleChoosePhoto}
            disabled={isPhotoProcessing}
          >
            {photoMutation.isPending && activePhotoAction === 'library' ? (
              <ActivityIndicator color="#1f2937" />
            ) : (
              <Text style={styles.secondaryButtonText}>
                Choose from library
              </Text>
            )}
          </Pressable>
          {photoStatus ? (
            <View style={styles.photoStatusRow}>
              <ActivityIndicator color="#2563eb" />
              <Text style={styles.photoStatusText}>{photoStatus}</Text>
            </View>
          ) : null}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border ?? 'rgba(0,0,0,0.1)',
  },
  closeButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 20,
  },
  closeButtonText: {
    fontSize: 24,
    fontWeight: '600',
    color: theme.colors.text,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: theme.colors.text,
  },
  headerSpacer: {
    width: 40,
  },
  content: {
    padding: 20,
  },
  heading: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 8,
  },
  description: {
    color: '#4b5563',
    marginBottom: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  primaryButton: {
    backgroundColor: '#2563eb',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: '#e5e7eb',
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  photoLibraryButton: {
    marginTop: 12,
  },
  secondaryButtonText: {
    color: '#1f2937',
    fontSize: 15,
    fontWeight: '500',
  },
  photoStatusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
  },
  photoStatusText: {
    marginLeft: 8,
    color: '#2563eb',
    flex: 1,
    fontWeight: '500',
  },
  input: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 10,
    padding: 12,
    backgroundColor: '#fff',
  },
  errorText: {
    color: '#dc2626',
    marginTop: 4,
  },
});
