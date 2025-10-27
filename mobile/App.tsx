/**
 * Main App Component for React Native Learning App
 *
 * Sets up navigation, providers, and global app state
 */

import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import type { Theme as NavigationTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

// Screens (using new modular structure)
import { LessonListScreen } from './modules/catalog/screens/UnitListScreen';
import { CatalogBrowserScreen } from './modules/catalog/screens/CatalogBrowserScreen';
import { LearningCoachScreen } from './modules/learning_coach/screens/LearningCoachScreen';
import LearningFlowScreen from './modules/learning_session/screens/LearningFlowScreen';
import ResultsScreen from './modules/learning_session/screens/ResultsScreen';
import { UnitDetailScreen } from './modules/catalog/screens/UnitDetailScreen';
import { UnitLODetailScreen } from './modules/catalog/screens/UnitLODetailScreen';
import LoginScreen from './modules/user/screens/LoginScreen';
import RegisterScreen from './modules/user/screens/RegisterScreen';
import ManageCacheScreen from './modules/offline_cache/screens/ManageCacheScreen';
import SQLiteDetailScreen from './modules/offline_cache/screens/SQLiteDetailScreen';
import AsyncStorageDetailScreen from './modules/offline_cache/screens/AsyncStorageDetailScreen';
import FileSystemDetailScreen from './modules/offline_cache/screens/FileSystemDetailScreen';

// Types
import type { RootStackParamList, LearningStackParamList } from './types';

// Theme (using new modular structure)
import { uiSystemProvider } from './modules/ui_system/public';
import { reducedMotion } from './modules/ui_system/utils/motion';
import { AuthProvider, useAuth } from './modules/user/public';
import { useTrackPlayer } from './modules/podcast_player/public';

// Create navigators
const RootStack = createNativeStackNavigator<RootStackParamList>();
const LearningStack = createNativeStackNavigator<LearningStackParamList>();

// Create QueryClient for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    },
  },
});

// Learning Stack Navigator
function LearningStackNavigator(): React.ReactElement {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  return (
    <LearningStack.Navigator
      id={undefined}
      screenOptions={{
        headerShown: false,
        animation: 'slide_from_right',
        animationDuration: 220,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <LearningStack.Screen
        name="LessonList"
        component={LessonListScreen}
        options={{
          title: 'Learning Lessons',
        }}
      />
      <LearningStack.Screen
        name="CatalogBrowser"
        component={CatalogBrowserScreen}
        options={{
          presentation: 'modal',
          animation: reducedMotion.enabled ? 'none' : 'slide_from_bottom',
          gestureDirection: 'vertical',
          headerShown: false,
        }}
      />
      <LearningStack.Screen
        name="LearningCoach"
        component={LearningCoachScreen}
        options={{
          title: 'Learning Coach',
        }}
      />
      <LearningStack.Screen
        name="UnitDetail"
        component={UnitDetailScreen}
        options={{
          title: 'Unit',
        }}
      />
      <LearningStack.Screen
        name="UnitLODetail"
        component={UnitLODetailScreen}
        options={{
          title: 'Learning Objectives',
        }}
      />
      <LearningStack.Screen
        name="ManageCache"
        component={ManageCacheScreen}
        options={{
          title: 'Manage Cache',
        }}
      />
      <LearningStack.Screen
        name="SQLiteDetail"
        component={SQLiteDetailScreen}
        options={{
          title: 'SQLite Database',
        }}
      />
      <LearningStack.Screen
        name="AsyncStorageDetail"
        component={AsyncStorageDetailScreen}
        options={{
          title: 'AsyncStorage',
        }}
      />
      <LearningStack.Screen
        name="FileSystemDetail"
        component={FileSystemDetailScreen}
        options={{
          title: 'File System',
        }}
      />
      <LearningStack.Screen
        name="LearningFlow"
        component={LearningFlowScreen}
        options={{
          title: 'Learning Session',
          gestureEnabled: false, // Prevent swipe back during learning
        }}
      />
      <LearningStack.Screen
        name="Results"
        component={ResultsScreen}
        options={{
          title: 'Results',
          gestureEnabled: false, // Prevent swipe back from results
        }}
      />
    </LearningStack.Navigator>
  );
}

// Main App Navigator
function RootNavigator(): React.ReactElement {
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const { user, isHydrated } = useAuth();

  if (!isHydrated) {
    return (
      <View
        style={[
          styles.loadingContainer,
          { backgroundColor: theme.colors.background },
        ]}
      >
        <ActivityIndicator color={theme.colors.primary} size="large" />
      </View>
    );
  }

  return (
    <RootStack.Navigator
      id={undefined}
      screenOptions={{
        headerShown: false,
        animation: 'slide_from_right',
        animationDuration: 220,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      {!user ? (
        <>
          <RootStack.Screen name="Login" component={LoginScreen} />
          <RootStack.Screen name="Register" component={RegisterScreen} />
        </>
      ) : (
        <>
          <RootStack.Screen
            name="Dashboard"
            component={LearningStackNavigator}
          />
          <RootStack.Screen
            name="LessonDetail"
            component={LearningFlowScreen as any}
            options={{ gestureEnabled: false }}
          />
        </>
      )}
    </RootStack.Navigator>
  );
}

export default function App(): React.ReactElement {
  // Get theme from ui_system module
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();
  const { isDarkMode } = uiSystem.getThemeState();

  // Initialize reduced motion once at app start (guarded for tests)
  (reducedMotion as any).initialize?.();

  useTrackPlayer();

  const navigationTheme: NavigationTheme = {
    ...DefaultTheme,
    dark: isDarkMode,
    colors: {
      ...DefaultTheme.colors,
      primary: theme.colors.primary,
      background: theme.colors.background,
      card: theme.colors.surface,
      text: theme.colors.text,
      border: theme.colors.border,
      notification: theme.colors.accent,
    },
  };

  return (
    // eslint-disable-next-line react-native/no-inline-styles
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <NavigationContainer theme={navigationTheme}>
            <StatusBar
              style={
                uiSystem.isLightColor(theme.colors.surface) ? 'dark' : 'light'
              }
              backgroundColor={theme.colors.surface}
              translucent={false}
            />
            <RootNavigator />
          </NavigationContainer>
        </AuthProvider>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
