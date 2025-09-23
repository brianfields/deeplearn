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
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { Difficulty } from '../models';
import { useCreateUnit } from '../queries';

interface CreateUnitFormData {
  topic: string;
  difficulty: Difficulty;
  targetLessonCount: number | null;
}

interface CreateUnitErrors {
  topic?: string;
  difficulty?: string;
  targetLessonCount?: string;
}

export function CreateUnitScreen() {
  const navigation = useNavigation();
  const createUnit = useCreateUnit();

  const [formData, setFormData] = useState<CreateUnitFormData>({
    topic: '',
    difficulty: 'beginner',
    targetLessonCount: null,
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

    console.log('Starting unit creation with data:', {
      topic: formData.topic.trim(),
      difficulty: formData.difficulty,
      targetLessonCount: formData.targetLessonCount,
    });

    try {
      const response = await createUnit.mutateAsync({
        topic: formData.topic.trim(),
        difficulty: formData.difficulty,
        targetLessonCount: formData.targetLessonCount,
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
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Create New Unit</Text>
          <Text style={styles.subtitle}>
            Tell us what you&apos;d like to learn and we&apos;ll create a
            personalized unit for you.
          </Text>
        </View>

        <View style={styles.form}>
          {/* Topic Input */}
          <View style={styles.fieldContainer}>
            <Text style={styles.fieldLabel}>Topic *</Text>
            <TextInput
              style={[styles.textInput, errors.topic && styles.textInputError]}
              placeholder="e.g., JavaScript Promises, Ancient Rome, Quantum Physics"
              placeholderTextColor="#8E8E93"
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
              <Text style={styles.errorText}>{errors.topic}</Text>
            )}
          </View>

          {/* Difficulty Selection */}
          <View style={styles.fieldContainer}>
            <Text style={styles.fieldLabel}>Difficulty Level</Text>
            <View style={styles.difficultyContainer}>
              {difficultyOptions.map(option => (
                <TouchableOpacity
                  key={option.value}
                  style={[
                    styles.difficultyOption,
                    formData.difficulty === option.value &&
                      styles.difficultyOptionSelected,
                  ]}
                  onPress={() =>
                    setFormData({ ...formData, difficulty: option.value })
                  }
                  disabled={isSubmitting}
                >
                  <Text
                    style={[
                      styles.difficultyText,
                      formData.difficulty === option.value &&
                        styles.difficultyTextSelected,
                    ]}
                  >
                    {option.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Target Lesson Count */}
          <View style={styles.fieldContainer}>
            <Text style={styles.fieldLabel}>
              Target Lesson Count (Optional)
            </Text>
            <TextInput
              style={[
                styles.textInput,
                styles.numberInput,
                errors.targetLessonCount && styles.textInputError,
              ]}
              placeholder="5"
              placeholderTextColor="#8E8E93"
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
              <Text style={styles.errorText}>{errors.targetLessonCount}</Text>
            )}
            <Text style={styles.helperText}>
              Leave blank to let AI decide the optimal number of lessons
            </Text>
          </View>
        </View>
      </ScrollView>

      {/* Action Buttons */}
      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={[styles.button, styles.cancelButton]}
          onPress={handleCancel}
          disabled={isSubmitting}
        >
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.button,
            styles.createButton,
            (!formData.topic.trim() || isSubmitting) &&
              styles.createButtonDisabled,
          ]}
          onPress={handleSubmit}
          disabled={!formData.topic.trim() || isSubmitting}
        >
          <View style={styles.buttonContent}>
            {isSubmitting && (
              <ActivityIndicator
                size="small"
                color="#FFFFFF"
                style={styles.buttonSpinner}
              />
            )}
            <Text style={styles.createButtonText}>
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
    backgroundColor: '#FFFFFF',
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
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#8E8E93',
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
    color: '#1C1C1E',
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#D1D1D6',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#1C1C1E',
    backgroundColor: '#FFFFFF',
    minHeight: 44,
  },
  numberInput: {
    minHeight: 44,
  },
  textInputError: {
    borderColor: '#FF3B30',
  },
  errorText: {
    color: '#FF3B30',
    fontSize: 14,
    marginTop: 4,
  },
  helperText: {
    color: '#8E8E93',
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
    borderColor: '#D1D1D6',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  difficultyOptionSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#E3F2FD',
  },
  difficultyText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1C1C1E',
  },
  difficultyTextSelected: {
    color: '#007AFF',
  },
  buttonContainer: {
    flexDirection: 'row',
    padding: 20,
    paddingTop: 16,
    gap: 12,
    borderTopWidth: 1,
    borderTopColor: '#F2F2F7',
    backgroundColor: '#FFFFFF',
  },
  button: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelButton: {
    backgroundColor: '#F2F2F7',
    borderWidth: 1,
    borderColor: '#D1D1D6',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  createButton: {
    backgroundColor: '#007AFF',
  },
  createButtonDisabled: {
    backgroundColor: '#C7C7CC',
  },
  createButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
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
