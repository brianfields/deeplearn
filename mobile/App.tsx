/**
 * Main App Component for React Native Learning App
 *
 * Sets up navigation, providers, and global app state
 */

import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Screens (using new modular structure)
import { LessonListScreen } from './modules/unit_catalog/screens/UnitListScreen';
import LearningFlowScreen from './modules/learning_session/screens/LearningFlowScreen';
import ResultsScreen from './modules/learning_session/screens/ResultsScreen';
import { UnitDetailScreen } from './modules/unit_catalog/screens/UnitDetailScreen';

// Types
import type { RootStackParamList, LearningStackParamList } from './types';

// Theme (using new modular structure)
import { uiSystemProvider } from './modules/ui_system/public';

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
function LearningStackNavigator() {
  return (
    <LearningStack.Navigator
      id={undefined}
      screenOptions={{
        headerShown: false,
        animation: 'slide_from_right',
        animationDuration: 300,
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
        name="UnitDetail"
        component={UnitDetailScreen}
        options={{
          title: 'Unit',
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
function RootNavigator() {
  return (
    <RootStack.Navigator
      id={undefined}
      screenOptions={{
        headerShown: false,
        animation: 'slide_from_right',
        animationDuration: 300,
      }}
    >
      <RootStack.Screen name="Dashboard" component={LearningStackNavigator} />
      <RootStack.Screen
        name="LessonDetail"
        component={LearningFlowScreen as any}
        options={{
          gestureEnabled: false, // Prevent swipe back during learning
        }}
      />
    </RootStack.Navigator>
  );
}

export default function App() {
  // Get theme from ui_system module
  const uiSystem = uiSystemProvider();
  const theme = uiSystem.getCurrentTheme();

  return (
    // eslint-disable-next-line react-native/no-inline-styles
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <NavigationContainer
          theme={{
            dark: false,
            colors: {
              primary: theme.colors.primary,
              background: theme.colors.background,
              card: theme.colors.surface,
              text: theme.colors.text,
              border: theme.colors.border,
              notification: theme.colors.accent,
            },
            fonts: {
              regular: {
                fontFamily: 'System',
                fontWeight: 'normal',
              },
              medium: {
                fontFamily: 'System',
                fontWeight: '500',
              },
              bold: {
                fontFamily: 'System',
                fontWeight: 'bold',
              },
              heavy: {
                fontFamily: 'System',
                fontWeight: '700',
              },
            },
          }}
        >
          <StatusBar
            style="dark"
            backgroundColor={theme.colors.surface}
            translucent={false}
          />
          <RootNavigator />
        </NavigationContainer>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
