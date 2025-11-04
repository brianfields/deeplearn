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
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button, Text, uiSystemProvider } from '../../ui_system/public';
import { useLogin } from '../queries';
import type { Theme } from '../../ui_system/models';
import { useAuth } from '../context';
import type { RootStackParamList } from '../../../types';

type LoginScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'Login'
>;

export default function LoginScreen() {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const navigation = useNavigation<LoginScreenNavigationProp>();
  const auth = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const loginMutation = useLogin();

  const handleSubmit = async () => {
    try {
      const user = await loginMutation.mutateAsync({ email, password });
      await auth.signIn(user);
    } catch (error: any) {
      const message = error?.message ?? 'Unable to login. Please try again.';
      Alert.alert('Login failed', message);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} testID="login-screen">
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.select({ ios: 'padding', android: undefined })}
      >
        <View style={styles.header}>
          <Text variant="h1" style={styles.title}>
            Welcome back
          </Text>
          <Text
            variant="body"
            color={theme.colors.textSecondary}
            style={styles.subtitle}
          >
            Sign in to continue your learning
          </Text>
        </View>

        <View style={styles.formGroup}>
          <Text variant="body" style={styles.label}>
            Email
          </Text>
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
            testID="login-email-input"
          />
        </View>

        <View style={styles.formGroup}>
          <Text variant="body" style={styles.label}>
            Password
          </Text>
          <TextInput
            accessibilityLabel="Password"
            secureTextEntry
            style={styles.input}
            placeholder="••••••••"
            value={password}
            onChangeText={setPassword}
            editable={!loginMutation.isPending}
            testID="login-password-input"
          />
        </View>

        <Button
          title={loginMutation.isPending ? 'Signing in…' : 'Sign in'}
          onPress={handleSubmit}
          disabled={loginMutation.isPending}
          loading={loginMutation.isPending}
          testID="login-submit-button"
        />

        {loginMutation.isPending && (
          <View style={styles.loadingRow}>
            <ActivityIndicator />
            <Text variant="caption" style={styles.loadingText}>
              Authenticating…
            </Text>
          </View>
        )}

        <View style={styles.footer}>
          <Text variant="caption" style={styles.footerText}>
            Don&apos;t have an account?{' '}
            <Text
              variant="caption"
              style={[styles.footerText, styles.link]}
              onPress={() => navigation.navigate('Register')}
            >
              Create one
            </Text>
          </Text>
        </View>
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
      color: theme.colors.text,
      fontWeight: '600',
    },
    subtitle: {
      opacity: 0.75,
    },
    formGroup: {
      marginBottom: 20,
    },
    label: {
      marginBottom: 6,
      opacity: 0.8,
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
      color: theme.colors.textSecondary,
    },
    footer: {
      marginTop: 32,
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
