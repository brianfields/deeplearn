import React, { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  StyleSheet,
  TextInput,
  View,
} from 'react-native';
import { Button, Text, uiSystemProvider } from '../../ui_system/public';
import { useLogin } from '../queries';
import type { Theme } from '../../ui_system/models';

interface Props {
  onLoginSuccess?: (userId: number) => void;
}

export default function LoginScreen({ onLoginSuccess }: Props) {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const loginMutation = useLogin();

  const handleSubmit = async () => {
    try {
      const user = await loginMutation.mutateAsync({ email, password });
      if (onLoginSuccess) {
        onLoginSuccess(user.id);
      }
    } catch (error: any) {
      const message = error?.message ?? 'Unable to login. Please try again.';
      Alert.alert('Login failed', message);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.select({ ios: 'padding', android: undefined })}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Welcome back</Text>
          <Text style={styles.subtitle}>Sign in to continue your learning</Text>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Email</Text>
          <TextInput
            accessibilityLabel="Email address"
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="email-address"
            style={styles.input}
            placeholder="you@example.com"
            value={email}
            onChangeText={setEmail}
            editable={!loginMutation.isPending}
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Password</Text>
          <TextInput
            accessibilityLabel="Password"
            secureTextEntry
            style={styles.input}
            placeholder="••••••••"
            value={password}
            onChangeText={setPassword}
            editable={!loginMutation.isPending}
          />
        </View>

        <Button
          title={loginMutation.isPending ? 'Signing in…' : 'Sign in'}
          onPress={handleSubmit}
          disabled={loginMutation.isPending}
          loading={loginMutation.isPending}
        />

        {loginMutation.isPending && (
          <View style={styles.loadingRow}>
            <ActivityIndicator />
            <Text style={styles.loadingText}>Authenticating…</Text>
          </View>
        )}
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
    container: {
      flex: 1,
      padding: 24,
      justifyContent: 'center',
    },
    header: {
      marginBottom: 32,
      gap: 4,
    },
    title: {
      fontSize: 28,
      fontWeight: '600',
      color: theme.colors.text,
    },
    subtitle: {
      fontSize: 16,
      opacity: 0.75,
      color: theme.colors.textSecondary,
    },
    formGroup: {
      marginBottom: 20,
    },
    label: {
      fontSize: 14,
      marginBottom: 6,
      opacity: 0.8,
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
    loadingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 12,
      marginTop: 20,
    },
    loadingText: {
      fontSize: 14,
      color: theme.colors.textSecondary,
    },
  });
