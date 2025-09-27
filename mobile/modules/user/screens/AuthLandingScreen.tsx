import React, { useMemo } from 'react';
import { SafeAreaView, StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Button, Text, uiSystemProvider } from '../../ui_system/public';
import type { Theme } from '../../ui_system/models';
import type { RootStackParamList } from '../../../types';

type AuthLandingNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'AuthLanding'
>;

export default function AuthLandingScreen(): React.ReactElement {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const navigation = useNavigation<AuthLandingNavigationProp>();

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: theme.colors.background }]}> 
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>DeepLearn</Text>
          <Text style={styles.subtitle}>
            Personalized learning journeys powered by AI. Sign in or create an
            account to get started.
          </Text>
        </View>

        <View style={styles.actions}>
          <Button
            title="Log in"
            size="large"
            fullWidth
            onPress={() => navigation.navigate('Login')}
          />
          <Button
            title="Create an account"
            variant="secondary"
            size="large"
            fullWidth
            onPress={() => navigation.navigate('Register')}
          />
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Need help? Contact support@deeplearn.app
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    safeArea: {
      flex: 1,
    },
    container: {
      flex: 1,
      padding: 24,
      justifyContent: 'space-between',
    },
    header: {
      marginTop: 32,
      gap: 16,
    },
    title: {
      fontSize: 32,
      fontWeight: '700',
      color: theme.colors.text,
    },
    subtitle: {
      fontSize: 16,
      color: theme.colors.textSecondary,
      lineHeight: 24,
    },
    actions: {
      gap: 16,
    },
    footer: {
      alignItems: 'center',
    },
    footerText: {
      fontSize: 13,
      color: theme.colors.textSecondary,
    },
  });
