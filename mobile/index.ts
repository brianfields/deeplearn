import 'react-native-gesture-handler';
import 'react-native-reanimated';
import { registerRootComponent } from 'expo';
import TrackPlayer from 'react-native-track-player';

import App from './App';

TrackPlayer.registerPlaybackService(
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  () => require('./modules/podcast_player/trackPlayerBackgroundService').default
);

// registerRootComponent calls AppRegistry.registerComponent('main', () => App);
// It also ensures that whether you load the app in Expo Go or in a native build,
// the environment is set up appropriately
registerRootComponent(App);
