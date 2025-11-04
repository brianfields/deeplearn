import React, { useMemo, useState } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  TextInput,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button, Text, uiSystemProvider } from '../../ui_system/public';
import type { Theme } from '../../ui_system/models';
import { useRegister } from '../queries';
import type { RootStackParamList } from '../../../types';

type RegisterScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'Register'
>;

export default function RegisterScreen() {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const navigation = useNavigation<RegisterScreenNavigationProp>();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const registerMutation = useRegister();

  const handleSubmit = async () => {
    if (password !== confirmPassword) {
      Alert.alert('Passwords do not match', 'Please confirm your password.');
      return;
    }

    try {
      await registerMutation.mutateAsync({
        email,
        password,
        name,
      });
      Alert.alert('Registration complete', 'You can now sign in.', [
        {
          text: 'Go to login',
          onPress: () => navigation.navigate('Login'),
        },
      ]);
      setName('');
      setEmail('');
      setPassword('');
      setConfirmPassword('');
    } catch (error: any) {
      const message = error?.message ?? 'Unable to complete registration.';
      Alert.alert('Registration failed', message);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.avoidingView}
        behavior={Platform.select({ ios: 'padding', android: undefined })}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <Text variant="h1" style={styles.title}>
              Create your account
            </Text>
            <Text variant="body" style={styles.subtitle}>
              Start building and tracking your learning journey.
            </Text>
          </View>

          <View style={styles.formGroup}>
            <Text variant="body" style={styles.label}>
              Full name
            </Text>
            <TextInput
              accessibilityLabel="Full name"
              style={styles.input}
              value={name}
              onChangeText={setName}
              placeholder="Ada Lovelace"
              editable={!registerMutation.isPending}
            />
          </View>

          <View style={styles.formGroup}>
            <Text variant="body" style={styles.label}>
              Email
            </Text>
            <TextInput
              accessibilityLabel="Email address"
              style={styles.input}
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="email-address"
              value={email}
              onChangeText={setEmail}
              placeholder="you@example.com"
              editable={!registerMutation.isPending}
            />
          </View>

          <View style={styles.formGroup}>
            <Text variant="body" style={styles.label}>
              Password
            </Text>
            <TextInput
              accessibilityLabel="Password"
              style={styles.input}
              secureTextEntry
              value={password}
              onChangeText={setPassword}
              placeholder="Use at least 8 characters"
              editable={!registerMutation.isPending}
            />
          </View>

          <View style={styles.formGroup}>
            <Text variant="body" style={styles.label}>
              Confirm password
            </Text>
            <TextInput
              accessibilityLabel="Confirm password"
              style={styles.input}
              secureTextEntry
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              placeholder="Repeat your password"
              editable={!registerMutation.isPending}
            />
          </View>

          <Button
            title={registerMutation.isPending ? 'Creating account…' : 'Sign up'}
            onPress={handleSubmit}
            disabled={registerMutation.isPending}
            loading={registerMutation.isPending}
          />

          <View style={styles.footer}>
            <Text variant="caption" style={styles.footerText}>
              Already have an account?{' '}
              <Text
                variant="caption"
                style={[styles.footerText, styles.link]}
                onPress={() => navigation.navigate('Login')}
              >
                Sign in
              </Text>
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    safeArea: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },
    avoidingView: {
      flex: 1,
    },
    scrollContent: {
      padding: 24,
      gap: 20,
    },
    header: {
      gap: 6,
      marginBottom: 12,
    },
    title: {
      fontWeight: '600',
      color: theme.colors.text,
    },
    subtitle: {
      color: theme.colors.textSecondary,
      opacity: 0.9,
    },
    formGroup: {
      gap: 6,
    },
    label: {
      color: theme.colors.textSecondary,
    },
    input: {
      borderRadius: 10,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.colors.border,
      paddingHorizontal: 14,
      paddingVertical: Platform.select({ ios: 14, android: 10 }),
      fontSize: 16,
      backgroundColor: theme.colors.surface,
      color: theme.colors.text,
    },
    footer: {
      marginTop: 24,
      alignItems: 'center',
    },
    footerText: {
      color: theme.colors.textSecondary,
    },
    link: {
      color: theme.colors.primary,
      fontWeight: '600',
    },
  });
