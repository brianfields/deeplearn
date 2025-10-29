import React, { useCallback, useState } from 'react';
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
  useAddResourceFromURL,
} from '../queries';
import type { ResourceSummary } from '../models';
import { ResourcePicker } from '../components/ResourcePicker';
import type { LearningStackParamList } from '../../../types';

const URL_REGEX = /^(https?:\/\/).+/i;

export type AddResourceScreenParams = {
  readonly attachToConversation?: boolean;
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
  const uploadMutation = useUploadResource();
  const urlMutation = useAddResourceFromURL();
  const resourcesQuery = useUserResources(userId, { enabled: !!userId });
  const attachToConversation = route.params?.attachToConversation ?? false;

  const handleResourceAttached = useCallback(
    (resourceId: string) => {
      if (!attachToConversation) {
        return;
      }
      // Update the LearningCoach screen params and go back to it
      navigation.navigate({
        name: 'LearningCoach',
        params: { attachResourceId: resourceId },
        merge: true, // Merge with existing params instead of replacing
      } as any);
    },
    [attachToConversation, navigation]
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
  }, [navigation, uploadMutation, userId]);

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
  }, [navigation, url, urlMutation, userId]);

  const handleSelectResource = useCallback(
    (resource: ResourceSummary) => {
      if (attachToConversation) {
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
    [attachToConversation, handleResourceAttached, navigation]
  );

  const handlePhotoPlaceholder = useCallback(() => {
    Alert.alert(
      'Coming soon',
      'Taking a photo as a resource will arrive in a future update.'
    );
  }, []);

  const isBusy = uploadMutation.isPending || urlMutation.isPending;

  return (
    <SafeAreaView style={styles.container}>
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
          />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Take a photo</Text>
          <Pressable
            style={styles.secondaryButton}
            onPress={handlePhotoPlaceholder}
          >
            <Text style={styles.secondaryButtonText}>Coming soon</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
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
  secondaryButtonText: {
    color: '#1f2937',
    fontSize: 15,
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
