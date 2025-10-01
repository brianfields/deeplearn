import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View,
  StyleSheet,
  Pressable,
  LayoutChangeEvent,
  GestureResponderEvent,
  ScrollView,
} from 'react-native';
import {
  Box,
  Card,
  Text,
  Button,
  uiSystemProvider,
  useHaptics,
} from '../../ui_system/public';
import type { PodcastTrack, PlaybackSpeed } from '../models';
import { usePodcastPlayer } from '../hooks/usePodcastPlayer';
import { usePodcastState } from '../hooks/usePodcastState';
import { PLAYBACK_SPEEDS } from '../store';

interface FullPlayerProps {
  readonly track: PodcastTrack;
  readonly onClose?: () => void;
}

function formatTime(totalSeconds: number): string {
  if (!Number.isFinite(totalSeconds) || totalSeconds < 0) {
    return '0:00';
  }
  const seconds = Math.floor(totalSeconds % 60)
    .toString()
    .padStart(2, '0');
  const minutes = Math.floor(totalSeconds / 60);
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  if (hours > 0) {
    return `${hours}:${remainingMinutes.toString().padStart(2, '0')}:${seconds}`;
  }
  return `${remainingMinutes}:${seconds}`;
}

export function FullPlayer({
  track,
  onClose,
}: FullPlayerProps): React.ReactElement {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const haptics = useHaptics();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const {
    loadTrack,
    play,
    pause,
    skipBackward,
    skipForward,
    seekTo,
    setSpeed,
    currentTrack,
    globalSpeed,
  } = usePodcastPlayer();
  const { playbackState: globalPlaybackState } = usePodcastState();

  const isCurrentTrack = currentTrack?.unitId === track.unitId;
  const effectivePlaybackState = isCurrentTrack
    ? globalPlaybackState
    : {
        position: 0,
        duration: track.durationSeconds,
        buffered: 0,
        isPlaying: false,
        isLoading: false,
      };

  const [progressWidth, setProgressWidth] = useState(0);
  const [transcriptExpanded, setTranscriptExpanded] = useState(false);

  useEffect(() => {
    if (!track || isCurrentTrack) {
      return;
    }
    loadTrack(track).catch(error => {
      console.warn('[PodcastPlayer] Failed to load track', error);
    });
  }, [isCurrentTrack, loadTrack, track]);

  const handlePlayPause = useCallback(async () => {
    haptics.trigger('light');
    if (!isCurrentTrack) {
      await loadTrack(track);
    }
    if (effectivePlaybackState.isPlaying) {
      await pause();
    } else {
      await play();
    }
  }, [
    effectivePlaybackState.isPlaying,
    haptics,
    isCurrentTrack,
    loadTrack,
    pause,
    play,
    track,
  ]);

  const onProgressLayout = useCallback((event: LayoutChangeEvent) => {
    setProgressWidth(event.nativeEvent.layout.width);
  }, []);

  const handleSeek = useCallback(
    async (event: GestureResponderEvent) => {
      if (!progressWidth) {
        return;
      }
      const ratio = event.nativeEvent.locationX / progressWidth;
      const duration =
        effectivePlaybackState.duration || track.durationSeconds || 0;
      const nextPosition = Math.max(0, ratio * duration);
      await seekTo(nextPosition);
    },
    [
      effectivePlaybackState.duration,
      progressWidth,
      seekTo,
      track.durationSeconds,
    ]
  );

  const handleSpeedPress = useCallback(
    async (speed: PlaybackSpeed) => {
      haptics.trigger('light');
      await setSpeed(speed);
    },
    [haptics, setSpeed]
  );

  const progressPercent = useMemo(() => {
    const duration =
      effectivePlaybackState.duration || track.durationSeconds || 0;
    if (!duration) {
      return 0;
    }
    return Math.min(1, effectivePlaybackState.position / duration);
  }, [
    effectivePlaybackState.duration,
    effectivePlaybackState.position,
    track.durationSeconds,
  ]);

  const isPlaying = effectivePlaybackState.isPlaying;
  const isLoading = effectivePlaybackState.isLoading;

  return (
    <Card variant="outlined" style={styles.card}>
      <Box mb="md">
        <View style={styles.headerRow}>
          <Text variant="title" style={styles.title}>
            {track.title}
          </Text>
          {onClose ? (
            <Button
              title="Close"
              onPress={() => {
                haptics.trigger('light');
                onClose();
              }}
              variant="secondary"
              size="small"
            />
          ) : null}
        </View>
        <Text variant="secondary" color={theme.colors.textSecondary}>
          {formatTime(track.durationSeconds)} total runtime
        </Text>
      </Box>

      <Box mb="lg">
        <Pressable
          onLayout={onProgressLayout}
          onPress={handleSeek}
          style={styles.progressBar}
          accessibilityRole="adjustable"
          accessibilityLabel="Seek podcast"
        >
          <View style={styles.progressTrack}>
            <View
              style={[
                styles.progressFill,
                { width: `${progressPercent * 100}%` },
              ]}
            />
          </View>
        </Pressable>
        <View style={styles.timeRow}>
          <Text variant="caption" color={theme.colors.textSecondary}>
            {formatTime(effectivePlaybackState.position)}
          </Text>
          <Text variant="caption" color={theme.colors.textSecondary}>
            {formatTime(
              effectivePlaybackState.duration || track.durationSeconds || 0
            )}
          </Text>
        </View>
      </Box>

      <View style={styles.controlsRow}>
        <Pressable
          style={[styles.controlButton, styles.secondaryControl]}
          onPress={() => {
            haptics.trigger('light');
            skipBackward().catch(() => {});
          }}
          accessibilityRole="button"
          accessibilityLabel="Skip backward 15 seconds"
        >
          <Text variant="body" style={styles.controlLabel}>
            −15s
          </Text>
        </Pressable>

        <Pressable
          style={[styles.controlButton, styles.primaryControl]}
          onPress={handlePlayPause}
          disabled={isLoading}
          accessibilityRole="button"
          accessibilityLabel={isPlaying ? 'Pause podcast' : 'Play podcast'}
        >
          <Text variant="title" style={styles.playLabel}>
            {isLoading ? '…' : isPlaying ? 'Pause' : 'Play'}
          </Text>
        </Pressable>

        <Pressable
          style={[styles.controlButton, styles.secondaryControl]}
          onPress={() => {
            haptics.trigger('light');
            skipForward().catch(() => {});
          }}
          accessibilityRole="button"
          accessibilityLabel="Skip forward 15 seconds"
        >
          <Text variant="body" style={styles.controlLabel}>
            +15s
          </Text>
        </Pressable>
      </View>

      <View style={styles.speedRow}>
        <Text variant="secondary" color={theme.colors.textSecondary}>
          Speed
        </Text>
        <View style={styles.speedOptions}>
          {PLAYBACK_SPEEDS.map(speed => {
            const isActive = globalSpeed === speed;
            return (
              <Pressable
                key={speed}
                style={[
                  styles.speedChip,
                  isActive && {
                    backgroundColor: theme.colors.primary,
                    borderColor: theme.colors.primary,
                  },
                ]}
                onPress={() => handleSpeedPress(speed)}
                accessibilityRole="button"
                accessibilityState={{ selected: isActive }}
              >
                <Text
                  variant="caption"
                  style={[
                    styles.speedChipLabel,
                    isActive && { color: theme.colors.surface },
                  ]}
                >
                  {speed
                    .toFixed(speed < 1 ? 2 : 2)
                    .replace(/0+$/, '')
                    .replace(/\.$/, '')}
                  x
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {track.transcript ? (
        <Box mt="lg">
          <Pressable
            onPress={() => {
              haptics.trigger('light');
              setTranscriptExpanded(prev => !prev);
            }}
            accessibilityRole="button"
            style={styles.transcriptToggle}
          >
            <Text variant="title" style={styles.transcriptTitle}>
              Transcript
            </Text>
            <Text variant="caption" color={theme.colors.textSecondary}>
              {transcriptExpanded ? 'Hide' : 'Show'}
            </Text>
          </Pressable>
          {transcriptExpanded ? (
            <ScrollView style={styles.transcriptContainer}>
              <Text variant="body" style={styles.transcriptText}>
                {track.transcript}
              </Text>
            </ScrollView>
          ) : (
            <Text
              variant="body"
              numberOfLines={3}
              style={styles.transcriptPreview}
            >
              {track.transcript}
            </Text>
          )}
        </Box>
      ) : null}
    </Card>
  );
}

const createStyles = (theme: any) =>
  StyleSheet.create({
    card: {
      padding: theme.spacing?.lg || 16,
    },
    headerRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: theme.spacing?.xs || 8,
    },
    title: {
      flex: 1,
      marginRight: theme.spacing?.md || 12,
    },
    progressBar: {
      width: '100%',
      paddingVertical: 8,
    },
    progressTrack: {
      height: 6,
      borderRadius: 4,
      backgroundColor: theme.colors.border,
      overflow: 'hidden',
    },
    progressFill: {
      height: '100%',
      backgroundColor: theme.colors.primary,
    },
    timeRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginTop: 4,
    },
    controlsRow: {
      flexDirection: 'row',
      justifyContent: 'space-around',
      alignItems: 'center',
      marginTop: theme.spacing?.md || 16,
    },
    controlButton: {
      width: 96,
      height: 96,
      borderRadius: 48,
      justifyContent: 'center',
      alignItems: 'center',
      borderWidth: 1,
      borderColor: theme.colors.border,
      backgroundColor: theme.colors.surface,
    },
    primaryControl: {
      width: 112,
      height: 112,
      borderRadius: 56,
      backgroundColor: theme.colors.primary,
      borderColor: theme.colors.primary,
    },
    secondaryControl: {
      backgroundColor: theme.colors.surface,
    },
    controlLabel: {
      color: theme.colors.text,
      fontWeight: '600',
    },
    playLabel: {
      color: theme.colors.surface,
      fontWeight: '600',
    },
    speedRow: {
      marginTop: theme.spacing?.lg || 20,
    },
    speedOptions: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: theme.spacing?.sm || 8,
      marginTop: theme.spacing?.sm || 8,
    },
    speedChip: {
      paddingHorizontal: theme.spacing?.md || 12,
      paddingVertical: theme.spacing?.xs || 6,
      borderRadius: 16,
      borderWidth: 1,
      borderColor: theme.colors.border,
      backgroundColor: theme.colors.surface,
    },
    speedChipLabel: {
      color: theme.colors.text,
      fontWeight: '500',
    },
    transcriptToggle: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    transcriptTitle: {
      fontWeight: '500',
    },
    transcriptContainer: {
      maxHeight: 220,
      marginTop: theme.spacing?.sm || 8,
    },
    transcriptPreview: {
      marginTop: theme.spacing?.sm || 8,
      color: theme.colors.text,
    },
    transcriptText: {
      color: theme.colors.text,
      lineHeight: 20,
    },
  });
