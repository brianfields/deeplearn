/**
 * Create Unit Screen
 *
 * Form for creating a new learning unit from a topic.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Switch,
} from 'react-native';
import { uiSystemProvider, useHaptics } from '../../ui_system/public';
import { useNavigation } from '@react-navigation/native';
import type { Difficulty } from '../models';
import { useCreateUnit } from '../queries';
import { useAuth } from '../../user/public';

interface CreateUnitFormData {
  topic: string;
  learner_level: Difficulty;
  targetLessonCount: number | null;
  shareGlobally: boolean;
}

interface CreateUnitErrors {
  topic?: string;
  learner_level?: string;
  targetLessonCount?: string;
}

export function CreateUnitScreen() {
  const navigation = useNavigation();
  const createUnit = useCreateUnit();
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const haptics = useHaptics();
  const { user } = useAuth();
  const currentUserId = user?.id;

  const [formData, setFormData] = useState<CreateUnitFormData>({
    topic: '',
    learner_level: 'beginner',
    targetLessonCount: null,
    shareGlobally: false,
  });

  const [errors, setErrors] = useState<CreateUnitErrors>({});

  const difficultyOptions: Array<{ value: Difficulty; label: string }> = [
    { value: 'beginner', label: 'Beginner' },
    { value: 'intermediate', label: 'Intermediate' },
    { value: 'advanced', label: 'Advanced' },
  ];

  const validateForm = (): boolean => {
    const newErrors: CreateUnitErrors = {};

    if (!formData.topic.trim()) {
      newErrors.topic = 'Topic is required';
    } else if (formData.topic.trim().length < 3) {
      newErrors.topic = 'Topic must be at least 3 characters long';
    }

    if (
      formData.targetLessonCount !== null &&
      (formData.targetLessonCount < 1 || formData.targetLessonCount > 20)
    ) {
      newErrors.targetLessonCount =
        'Target lesson count must be between 1 and 20';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    if (!currentUserId) {
      Alert.alert('Sign in required', 'Please log in to create a unit.');
      return;
    }

    haptics.trigger('medium');

    console.log('Starting unit creation with data:', {
      topic: formData.topic.trim(),
      learner_level: formData.learner_level,
      targetLessonCount: formData.targetLessonCount,
    });

    try {
      const response = await createUnit.mutateAsync({
        topic: formData.topic.trim(),
        difficulty: formData.learner_level,
        targetLessonCount: formData.targetLessonCount,
        shareGlobally: formData.shareGlobally,
        ownerUserId: currentUserId,
      });

      console.log('Unit creation response:', response);

      // Navigate back immediately and show success message
      navigation.goBack();

      // Show a brief success alert that doesn't block navigation
      setTimeout(() => {
        Alert.alert(
          'Unit Creation Started! 🎉',
          `Your unit "${response.title}" is being created in the background. You can track its progress in the Units list.`,
          [{ text: 'Got it!' }]
        );
      }, 100);
    } catch (error: any) {
      console.error('Unit creation error:', error);

      // Extract more detailed error information
      const errorMessage =
        error?.message ||
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        'Failed to create unit. Please try again.';

      Alert.alert('Creation Failed', errorMessage, [{ text: 'OK' }]);
    }
  };

  const handleCancel = () => {
    haptics.trigger('light');
    if (formData.topic.trim()) {
      Alert.alert(
        'Cancel Creation',
        'Are you sure you want to cancel? Your input will be lost.',
        [
          { text: 'Continue Editing', style: 'cancel' },
          {
            text: 'Cancel',
            style: 'destructive',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } else {
      navigation.goBack();
    }
  };

  const isSubmitting = createUnit.isPending;

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
      >
        <View style={styles.header}>
          <Text
            style={[
              styles.title,
              { color: theme.colors.text, fontWeight: 'normal' },
            ]}
          >
            Create New Unit
          </Text>
          <Text
            style={[styles.subtitle, { color: theme.colors.textSecondary }]}
          >
            Tell us what you&apos;d like to learn and we&apos;ll create a
            personalized unit for you.
          </Text>
        </View>

        <View style={styles.form}>
          {/* Topic Input */}
          <View style={styles.fieldContainer}>
            <Text
              style={[
                styles.fieldLabel,
                { color: theme.colors.text, fontWeight: 'normal' },
              ]}
            >
              Topic *
            </Text>
            <TextInput
              style={[
                styles.textInput,
                {
                  color: theme.colors.text,
                  backgroundColor: theme.colors.surface,
                  borderColor: theme.colors.border,
                },
                errors.topic && { borderColor: theme.colors.error },
              ]}
              placeholder="e.g., JavaScript Promises, Ancient Rome, Quantum Physics"
              placeholderTextColor={theme.colors.textSecondary}
              value={formData.topic}
              onChangeText={text => {
                setFormData({ ...formData, topic: text });
                if (errors.topic) {
                  setErrors({ ...errors, topic: undefined });
                }
              }}
              multiline
              numberOfLines={3}
              textAlignVertical="top"
              editable={!isSubmitting}
            />
            {errors.topic && (
              <Text style={[styles.errorText, { color: theme.colors.error }]}>
                {errors.topic}
              </Text>
            )}
          </View>

          {/* Learner Level Selection */}
          <View style={styles.fieldContainer}>
            <Text
              style={[
                styles.fieldLabel,
                { color: theme.colors.text, fontWeight: 'normal' },
              ]}
            >
              Learner Level
            </Text>
            <View style={styles.difficultyContainer}>
              {difficultyOptions.map(option => (
                <TouchableOpacity
                  key={option.value}
                  style={[
                    styles.difficultyOption,
                    {
                      borderColor: theme.colors.border,
                      backgroundColor: theme.colors.surface,
                    },
                    formData.learner_level === option.value && {
                      borderColor: theme.colors.primary,
                      backgroundColor: `${theme.colors.primary}1A`,
                    },
                  ]}
                  onPress={() => {
                    haptics.trigger('medium');
                    setFormData({ ...formData, learner_level: option.value });
                  }}
                  disabled={isSubmitting}
                >
                  <Text
                    style={[
                      styles.difficultyText,
                      { color: theme.colors.text },
                      formData.learner_level === option.value && {
                        color: theme.colors.primary,
                      },
                    ]}
                  >
                    {option.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Share globally toggle */}
          <View style={styles.fieldContainer}>
            <View style={styles.toggleRow}>
              <Text
                style={[
                  styles.fieldLabel,
                  { color: theme.colors.text, fontWeight: 'normal' },
                ]}
              >
                Share globally
              </Text>
              <Switch
                value={formData.shareGlobally}
                onValueChange={value =>
                  setFormData(prev => ({ ...prev, shareGlobally: value }))
                }
              />
            </View>
            <Text style={{ color: theme.colors.textSecondary }}>
              {formData.shareGlobally
                ? 'This unit will be visible to all learners once created.'
                : 'Leave off to keep the unit personal to you.'}
            </Text>
          </View>

          {/* Target Lesson Count */}
          <View style={styles.fieldContainer}>
            <Text
              style={[
                styles.fieldLabel,
                { color: theme.colors.text, fontWeight: 'normal' },
              ]}
            >
              Target Lesson Count (Optional)
            </Text>
            <TextInput
              style={[
                styles.textInput,
                styles.numberInput,
                {
                  color: theme.colors.text,
                  backgroundColor: theme.colors.surface,
                  borderColor: theme.colors.border,
                },
                errors.targetLessonCount && { borderColor: theme.colors.error },
              ]}
              placeholder="5"
              placeholderTextColor={theme.colors.textSecondary}
              value={formData.targetLessonCount?.toString() || ''}
              onChangeText={text => {
                const num = text ? parseInt(text, 10) : null;
                setFormData({
                  ...formData,
                  targetLessonCount: isNaN(num!) ? null : num,
                });
                if (errors.targetLessonCount) {
                  setErrors({ ...errors, targetLessonCount: undefined });
                }
              }}
              keyboardType="number-pad"
              editable={!isSubmitting}
            />
            {errors.targetLessonCount && (
              <Text style={[styles.errorText, { color: theme.colors.error }]}>
                {errors.targetLessonCount}
              </Text>
            )}
            <Text
              style={[styles.helperText, { color: theme.colors.textSecondary }]}
            >
              Leave blank to let AI decide the optimal number of lessons
            </Text>
          </View>
        </View>
      </ScrollView>

      {/* Action Buttons */}
      <View
        style={[
          styles.buttonContainer,
          {
            borderTopColor: theme.colors.border,
            backgroundColor: theme.colors.surface,
          },
        ]}
      >
        <TouchableOpacity
          style={[
            styles.button,
            {
              backgroundColor: theme.colors.border,
              borderColor: theme.colors.border,
            },
          ]}
          onPress={handleCancel}
          disabled={isSubmitting}
        >
          <Text style={[styles.cancelButtonText, { color: theme.colors.text }]}>
            Cancel
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.button,
            { backgroundColor: theme.colors.primary },
            (!formData.topic.trim() || isSubmitting) && {
              backgroundColor: theme.colors.border,
            },
          ]}
          onPress={handleSubmit}
          disabled={!formData.topic.trim() || isSubmitting}
        >
          <View style={styles.buttonContent}>
            {isSubmitting && (
              <ActivityIndicator
                size="small"
                color={theme.colors.surface}
                style={styles.buttonSpinner}
              />
            )}
            <Text
              style={[styles.createButtonText, { color: theme.colors.surface }]}
            >
              {isSubmitting ? 'Creating...' : 'Create Unit'}
            </Text>
          </View>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  header: {
    padding: 20,
    paddingBottom: 10,
  },
  title: {
    fontSize: 28,
    fontWeight: 'normal',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    lineHeight: 22,
  },
  form: {
    padding: 20,
    paddingTop: 10,
  },
  fieldContainer: {
    marginBottom: 24,
  },
  fieldLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    minHeight: 44,
  },
  numberInput: {
    minHeight: 44,
  },
  textInputError: {},
  errorText: {
    fontSize: 14,
    marginTop: 4,
  },
  helperText: {
    fontSize: 14,
    marginTop: 4,
  },
  difficultyContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  difficultyOption: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  difficultyOptionSelected: {},
  difficultyText: {
    fontSize: 16,
    fontWeight: '500',
  },
  difficultyTextSelected: {},
  buttonContainer: {
    flexDirection: 'row',
    padding: 20,
    paddingTop: 16,
    gap: 12,
    borderTopWidth: 1,
  },
  button: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelButton: {
    borderWidth: 1,
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  createButton: {},
  createButtonDisabled: {},
  createButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonSpinner: {
    marginRight: 8,
  },
});
