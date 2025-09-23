import { useCallback } from 'react';
import * as Haptics from 'expo-haptics';

export type HapticPattern = 'light' | 'medium' | 'success';

export function useHaptics() {
  const trigger = useCallback(async (pattern: HapticPattern) => {
    switch (pattern) {
      case 'light':
        await Haptics.selectionAsync();
        break;
      case 'medium':
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
        break;
      case 'success':
        await Haptics.notificationAsync(
          Haptics.NotificationFeedbackType.Success
        );
        break;
      default:
        break;
    }
  }, []);

  return { trigger };
}
