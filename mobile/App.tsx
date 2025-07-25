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

// Screens
import TopicListScreen from '@/screens/learning/TopicListScreen';
import LearningFlowScreen from '@/screens/learning/LearningFlowScreen';
import ResultsScreen from '@/screens/learning/ResultsScreen';

// Types
import type { RootStackParamList, LearningStackParamList } from '@/types';

// Theme
import { colors } from '@/utils/theme';

// Create navigators
const RootStack = createNativeStackNavigator<RootStackParamList>();
const LearningStack = createNativeStackNavigator<LearningStackParamList>();

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
        name="TopicList"
        component={TopicListScreen as any}
        options={{
          title: 'Learning Topics',
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
        name="Learning"
        component={LearningStackNavigator}
        options={{
          presentation: 'modal',
        }}
      />
      <RootStack.Screen
        name="TopicDetail"
        component={LearningFlowScreen as any}
        options={{
          presentation: 'modal',
        }}
      />
    </RootStack.Navigator>
  );
}

export default function App() {
  return (
    // eslint-disable-next-line react-native/no-inline-styles
    <GestureHandlerRootView style={{ flex: 1 }}>
      <NavigationContainer
        theme={{
          dark: false,
          colors: {
            primary: colors.primary,
            background: colors.background,
            card: colors.surface,
            text: colors.text,
            border: colors.border,
            notification: colors.accent,
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
          backgroundColor={colors.surface}
          translucent={false}
        />
        <RootNavigator />
      </NavigationContainer>
    </GestureHandlerRootView>
  );
}
