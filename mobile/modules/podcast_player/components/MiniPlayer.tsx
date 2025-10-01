import React, { useMemo } from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Text, uiSystemProvider, useHaptics } from '../../ui_system/public';
import { usePodcastPlayer } from '../hooks/usePodcastPlayer';
import { usePodcastState } from '../hooks/usePodcastState';

interface MiniPlayerProps {
  readonly unitId: string;
}

export function MiniPlayer({
  unitId,
}: MiniPlayerProps): React.ReactElement | null {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const haptics = useHaptics();
  const { playbackState, currentTrack, setMinimized } = usePodcastState();
  const { play, pause, skipBackward, skipForward } = usePodcastPlayer();

  if (!currentTrack || currentTrack.unitId !== unitId) {
    return null;
  }

  const isPlaying = playbackState.isPlaying;
  const progressPercent = playbackState.duration
    ? Math.min(1, playbackState.position / playbackState.duration)
    : 0;

  return (
    <View style={styles.container}>
      <View style={styles.progressTrack}>
        <View
          style={[styles.progressFill, { width: `${progressPercent * 100}%` }]}
        />
      </View>
      <View style={styles.contentRow}>
        <View style={styles.infoColumn}>
          <View style={styles.infoHeader}>
            <Text variant="caption" color={theme.colors.textSecondary}>
              Unit Podcast
            </Text>
            <Pressable
              onPress={() => {
                haptics.trigger('light');
                setMinimized(true);
              }}
              accessibilityRole="button"
              accessibilityLabel="Hide podcast controls"
              testID="mini-player-hide"
              style={styles.hideButton}
            >
              <Text variant="caption" style={styles.hideText}>
                Hide
              </Text>
            </Pressable>
          </View>
          <Text variant="body" numberOfLines={1} style={styles.title}>
            {currentTrack.title}
          </Text>
        </View>
        <View style={styles.controls}>
          <Pressable
            style={styles.iconButton}
            onPress={() => {
              haptics.trigger('light');
              skipBackward().catch(() => {});
            }}
            accessibilityRole="button"
            accessibilityLabel="Skip backward 15 seconds"
            testID="mini-player-skip-backward"
          >
            <Text variant="caption" style={styles.iconLabel}>
              −15
            </Text>
          </Pressable>
          <Pressable
            style={[styles.iconButton, styles.primaryButton]}
            onPress={() => {
              haptics.trigger('light');
              if (isPlaying) {
                pause().catch(() => {});
              } else {
                play().catch(() => {});
              }
            }}
            accessibilityRole="button"
            accessibilityLabel={isPlaying ? 'Pause podcast' : 'Play podcast'}
            testID="mini-player-toggle"
          >
            <Text variant="body" style={styles.playLabel}>
              {isPlaying ? 'Pause' : 'Play'}
            </Text>
          </Pressable>
          <Pressable
            style={styles.iconButton}
            onPress={() => {
              haptics.trigger('light');
              skipForward().catch(() => {});
            }}
            accessibilityRole="button"
            accessibilityLabel="Skip forward 15 seconds"
            testID="mini-player-skip-forward"
          >
            <Text variant="caption" style={styles.iconLabel}>
              +15
            </Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
}

const createStyles = (theme: any) =>
  StyleSheet.create({
    container: {
      position: 'absolute',
      left: theme.spacing?.lg || 16,
      right: theme.spacing?.lg || 16,
      bottom: theme.spacing?.lg || 16,
      minHeight: 68,
      borderRadius: 24,
      backgroundColor: `${theme.colors.surface}F0`,
      paddingVertical: theme.spacing?.sm || 10,
      paddingHorizontal: theme.spacing?.md || 16,
      shadowColor: theme.colors.text,
      shadowOpacity: 0.08,
      shadowRadius: 12,
      shadowOffset: { width: 0, height: 4 },
      elevation: 8,
    },
    progressTrack: {
      height: 3,
      borderRadius: 2,
      backgroundColor: theme.colors.border,
      overflow: 'hidden',
      marginBottom: theme.spacing?.xs || 6,
    },
    progressFill: {
      height: '100%',
      backgroundColor: theme.colors.primary,
    },
    contentRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: theme.spacing?.md || 16,
    },
    infoColumn: {
      flex: 1,
      marginRight: theme.spacing?.md || 12,
    },
    infoHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: theme.spacing?.xxs || 4,
    },
    title: {
      color: theme.colors.text,
      fontWeight: '600',
    },
    hideButton: {
      paddingHorizontal: theme.spacing?.xs || 8,
      paddingVertical: theme.spacing?.xxs || 4,
      borderRadius: 12,
      backgroundColor: `${theme.colors.border}55`,
    },
    hideText: {
      color: theme.colors.textSecondary,
      fontWeight: '500',
    },
    controls: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: theme.spacing?.xs || 8,
    },
    iconButton: {
      minWidth: 48,
      paddingVertical: 8,
      paddingHorizontal: 10,
      borderRadius: 20,
      backgroundColor: theme.colors.surface,
      borderWidth: 1,
      borderColor: theme.colors.border,
      alignItems: 'center',
      justifyContent: 'center',
    },
    primaryButton: {
      backgroundColor: theme.colors.primary,
      borderColor: theme.colors.primary,
    },
    iconLabel: {
      color: theme.colors.text,
      fontWeight: '600',
    },
    playLabel: {
      color: theme.colors.surface,
      fontWeight: '600',
    },
  });
