import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { ResourceLibraryScreen } from './screens/ResourceLibraryScreen';
import { ResourceDetailScreen } from './screens/ResourceDetailScreen';
import {
  AddResourceScreen,
  type AddResourceScreenParams,
} from './screens/AddResourceScreen';
import { getScreenOptions } from '../../utils/navigationOptions';

export type ResourceStackParamList = {
  ResourceLibrary: undefined;
  ResourceDetail: { resourceId: string };
  AddResource: AddResourceScreenParams | undefined;
};

const Stack = createNativeStackNavigator<ResourceStackParamList>();

/**
 * ResourceNavigator
 *
 * Nested navigator for resource management screens.
 * This can be integrated into the main LearningStack as a nested modal navigator
 * for future refactoring. Currently, AddResourceScreen is used directly in LearningStack.
 *
 * Usage:
 * <LearningStack.Screen
 *   name="Resources"
 *   component={ResourceNavigator}
 *   options={getScreenOptions('modal')}
 * />
 */
export function ResourceNavigator(): React.ReactElement {
  return (
    <Stack.Navigator
      screenOptions={{
        ...getScreenOptions('stack'),
        animationDuration: 220,
      }}
    >
      <Stack.Screen
        name="ResourceLibrary"
        component={ResourceLibraryScreen}
        options={{
          title: 'Resource Library',
        }}
      />
      <Stack.Screen
        name="ResourceDetail"
        component={ResourceDetailScreen}
        options={{
          title: 'Resource Detail',
        }}
      />
      <Stack.Screen
        name="AddResource"
        component={AddResourceScreen}
        options={{
          ...getScreenOptions('modal'),
          title: 'Add Resource',
        }}
      />
    </Stack.Navigator>
  );
}
