import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { ResourceLibraryScreen } from './screens/ResourceLibraryScreen';
import { ResourceDetailScreen } from './screens/ResourceDetailScreen';
import {
  AddResourceScreen,
  type AddResourceScreenParams,
} from './screens/AddResourceScreen';

export type ResourceStackParamList = {
  ResourceLibrary: undefined;
  ResourceDetail: { resourceId: string };
  AddResource: AddResourceScreenParams | undefined;
};

const Stack = createNativeStackNavigator<ResourceStackParamList>();

export function ResourceNavigator(): React.ReactElement {
  return (
    <Stack.Navigator>
      <Stack.Screen
        name="ResourceLibrary"
        component={ResourceLibraryScreen}
        options={{ title: 'Resource Library' }}
      />
      <Stack.Screen
        name="ResourceDetail"
        component={ResourceDetailScreen}
        options={{ title: 'Resource Detail' }}
      />
      <Stack.Screen
        name="AddResource"
        component={AddResourceScreen}
        options={{ title: 'Add Resource' }}
      />
    </Stack.Navigator>
  );
}
