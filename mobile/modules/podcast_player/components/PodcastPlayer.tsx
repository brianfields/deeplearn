import React, {
  useState,
  useMemo,
  useEffect,
  useRef,
  useCallback,
} from 'react';
import {
  View,
  StyleSheet,
  Pressable,
  ScrollView,
  PanResponder,
} from 'react-native';
import {
  Text,
  ArtworkImage,
  uiSystemProvider,
  useHaptics,
} from '../../ui_system/public';
import { usePodcastPlayer } from '../hooks/usePodcastPlayer';
import { usePodcastState } from '../hooks/usePodcastState';
import type { PodcastTrack } from '../models';
import { PLAYBACK_SPEEDS } from '../store';

interface PodcastPlayerProps {
  readonly track: PodcastTrack;
  readonly unitId: string;
  readonly defaultExpanded?: boolean;
}

export function PodcastPlayer({
  track,
  unitId,
  defaultExpanded = false,
}: PodcastPlayerProps): React.ReactElement {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const haptics = useHaptics();
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const { playbackState, currentTrack, globalSpeed } = usePodcastState();
  const {
    loadTrack,
    play,
    pause,
    skipBackward,
    skipForward,
    seekTo,
    setSpeed,
  } = usePodcastPlayer();

  const isCurrentTrack = currentTrack?.unitId === unitId;

  // Speed slider drag state
  const sliderWidth = useRef(0);
  const sliderX = useRef(0);
  const [isDraggingSpeed, setIsDraggingSpeed] = useState(false);
  const [dragSpeedPosition, setDragSpeedPosition] = useState(0);

  // Load track when component mounts (same as FullPlayer)
  useEffect(() => {
    if (!track || isCurrentTrack) {
      return;
    }
    loadTrack(track).catch(error => {
      console.warn('[PodcastPlayer] Failed to load track', error);
    });
  }, [isCurrentTrack, loadTrack, track]);

  const isPlaying = playbackState.isPlaying;
  const position = playbackState.position;
  const duration = playbackState.duration || track.durationSeconds;
  const progressPercent = duration > 0 ? position / duration : 0;

  // Map speed to slider position (0-1)
  const getSpeedPosition = (speed: number): number => {
    const index = PLAYBACK_SPEEDS.indexOf(speed as any);
    return index / (PLAYBACK_SPEEDS.length - 1);
  };

  // Map slider position to speed
  const getSpeedFromPosition = useCallback((positionRatio: number): number => {
    const index = Math.round(positionRatio * (PLAYBACK_SPEEDS.length - 1));
    return PLAYBACK_SPEEDS[
      Math.max(0, Math.min(PLAYBACK_SPEEDS.length - 1, index))
    ];
  }, []);

  const speedPosition = getSpeedPosition(globalSpeed);
  const displaySpeedPosition = isDraggingSpeed
    ? dragSpeedPosition
    : speedPosition;

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTogglePlay = (): void => {
    console.log(
      '[PodcastPlayer UI] Play button pressed, current isPlaying:',
      isPlaying
    );
    console.log('[PodcastPlayer UI] Current track:', currentTrack?.title);
    haptics.trigger('light');
    if (isPlaying) {
      console.log('[PodcastPlayer UI] Calling pause()');
      pause().catch(() => {});
    } else {
      console.log('[PodcastPlayer UI] Calling play()');
      play().catch(error => {
        console.error('[PodcastPlayer UI] Play error:', error);
      });
    }
  };

  const handleSkipBackward = (): void => {
    haptics.trigger('light');
    skipBackward().catch(() => {});
  };

  const handleSkipForward = (): void => {
    haptics.trigger('light');
    skipForward().catch(() => {});
  };

  const handleToggleExpand = (): void => {
    haptics.trigger('medium');
    setIsExpanded(!isExpanded);
  };

  const handleSeek = (percent: number): void => {
    const newPosition = percent * duration;
    seekTo(newPosition).catch(() => {});
  };

  const handleSpeedChange = useCallback(
    (speed: number): void => {
      haptics.trigger('light');
      setSpeed(speed as any).catch(() => {});
    },
    [haptics, setSpeed]
  );

  // Create pan responder for draggable speed slider
  const speedPanResponder = useMemo(
    () =>
      PanResponder.create({
        onStartShouldSetPanResponder: () => true,
        onMoveShouldSetPanResponder: () => true,
        onPanResponderGrant: () => {
          setIsDraggingSpeed(true);
          haptics.trigger('light');
        },
        onPanResponderMove: (_, gestureState) => {
          if (sliderWidth.current > 0 && sliderX.current !== undefined) {
            // Calculate position relative to slider start
            const relativeX = gestureState.moveX - sliderX.current;
            const position = Math.max(
              0,
              Math.min(1, relativeX / sliderWidth.current)
            );
            setDragSpeedPosition(position);
          }
        },
        onPanResponderRelease: () => {
          const newSpeed = getSpeedFromPosition(dragSpeedPosition);
          handleSpeedChange(newSpeed);
          setIsDraggingSpeed(false);
          haptics.trigger('medium');
        },
        onPanResponderTerminate: () => {
          setIsDraggingSpeed(false);
        },
      }),
    [dragSpeedPosition, getSpeedFromPosition, handleSpeedChange, haptics]
  );

  if (!isCurrentTrack) {
    return <View />;
  }

  return (
    <View style={styles.container}>
      {/* Collapsed Player Bar */}
      <View style={styles.collapsedBar}>
        {/* Expand Button */}
        <Pressable
          onPress={handleToggleExpand}
          style={styles.expandButton}
          accessibilityLabel={isExpanded ? 'Collapse player' : 'Expand player'}
          accessibilityRole="button"
        >
          <Text variant="h2" style={styles.expandIcon}>
            {isExpanded ? '⌄' : '⌃'}
          </Text>
        </Pressable>

        {/* Skip Backward */}
        <Pressable
          onPress={handleSkipBackward}
          style={styles.skipButton}
          accessibilityLabel="Skip backward 15 seconds"
          accessibilityRole="button"
        >
          <View style={styles.skipCircle}>
            <Text variant="caption" style={styles.skipText}>
              ‹15
            </Text>
          </View>
        </Pressable>

        {/* Play/Pause Button (centered) */}
        <Pressable
          onPress={handleTogglePlay}
          style={styles.playButton}
          accessibilityLabel={isPlaying ? 'Pause' : 'Play'}
          accessibilityRole="button"
        >
          <View
            style={[
              styles.playCircle,
              { backgroundColor: theme.colors.primary },
            ]}
          >
            <Text variant="h2" style={styles.playIcon}>
              {isPlaying ? '❚❚' : '▶'}
            </Text>
          </View>
        </Pressable>

        {/* Skip Forward */}
        <Pressable
          onPress={handleSkipForward}
          style={styles.skipButton}
          accessibilityLabel="Skip forward 15 seconds"
          accessibilityRole="button"
        >
          <View style={styles.skipCircle}>
            <Text variant="caption" style={styles.skipText}>
              15›
            </Text>
          </View>
        </Pressable>

        {/* Artwork */}
        <View style={styles.artworkContainer}>
          <ArtworkImage
            title={track.title}
            imageUrl={track.artworkUrl ?? undefined}
            variant="thumbnail"
          />
        </View>
      </View>

      {/* Expanded Player Content */}
      {isExpanded && (
        <ScrollView
          style={styles.expandedContent}
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.expandedInner}>
            {/* Title */}
            <Text variant="h2" style={styles.title}>
              {track.title}
            </Text>

            {/* Time Labels */}
            <View style={styles.timeRow}>
              <Text variant="caption" color={theme.colors.textSecondary}>
                {formatTime(position)}
              </Text>
              <Text variant="caption" color={theme.colors.textSecondary}>
                {formatTime(duration)}
              </Text>
            </View>

            {/* Progress Bar */}
            <View style={styles.progressContainer}>
              <View style={styles.progressTrack}>
                <View
                  style={[
                    styles.progressFill,
                    {
                      width: `${progressPercent * 100}%`,
                      backgroundColor: theme.colors.primary,
                    },
                  ]}
                />
              </View>
              <Pressable
                style={styles.progressTouchable}
                onPress={e => {
                  const { locationX } = e.nativeEvent;
                  const percent = locationX / 300; // Approximate width
                  handleSeek(percent);
                }}
              />
            </View>

            {/* Speed Controls - Overcast Style */}
            <View style={styles.speedSection}>
              <Text
                variant="caption"
                color={theme.colors.textSecondary}
                style={styles.sectionLabel}
              >
                Playback Speed
              </Text>

              {/* Speed markers */}
              <View style={styles.speedMarkers}>
                <Text style={[styles.speedMarker, styles.speedMarkerMuted]}>
                  −
                </Text>
                <Text style={styles.speedMarkerMain}>1×</Text>
                <Text style={styles.speedMarkerMuted}>+</Text>
                <Text style={styles.speedMarkerMuted}>+</Text>
                <Text style={styles.speedMarkerMuted}>+</Text>
                <Text style={styles.speedMarkerMuted}>+</Text>
                <Text style={styles.speedMarkerMuted}>+</Text>
                <Text style={styles.speedMarkerMain}>2×</Text>
                <Text style={styles.speedMarkerMuted}>+</Text>
                <Text style={styles.speedMarkerMain}>3×</Text>
              </View>

              {/* Speed slider */}
              <View
                style={styles.speedSliderContainer}
                onLayout={e => {
                  sliderWidth.current = e.nativeEvent.layout.width;
                  e.currentTarget.measure((x, y, width, height, pageX) => {
                    sliderX.current = pageX;
                  });
                }}
              >
                <View style={styles.speedSliderTrack}>
                  <View
                    style={[
                      styles.speedSliderFill,
                      {
                        width: `${displaySpeedPosition * 100}%`,
                        backgroundColor: theme.colors.primary,
                      },
                    ]}
                  />
                </View>
                <View
                  style={styles.speedSliderTouchable}
                  {...speedPanResponder.panHandlers}
                >
                  <View
                    style={[
                      styles.speedSliderThumb,
                      isDraggingSpeed && styles.speedSliderThumbActive,
                      {
                        left: `${displaySpeedPosition * 100}%`,
                      },
                    ]}
                  />
                </View>
              </View>

              {/* Current speed display */}
              <Text style={styles.currentSpeedText}>{globalSpeed}×</Text>
            </View>

            {/* Transcript */}
            {track.transcript && (
              <View style={styles.transcriptSection}>
                <Text
                  variant="caption"
                  color={theme.colors.textSecondary}
                  style={styles.sectionLabel}
                >
                  Transcript
                </Text>
                <Text
                  variant="body"
                  color={theme.colors.text}
                  style={styles.transcriptText}
                >
                  {track.transcript}
                </Text>
              </View>
            )}
          </View>
        </ScrollView>
      )}
    </View>
  );
}

const createStyles = (theme: any) =>
  StyleSheet.create({
    container: {
      position: 'absolute',
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: theme.colors.surface,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border,
      shadowColor: theme.colors.text,
      shadowOpacity: 0.1,
      shadowRadius: 8,
      shadowOffset: { width: 0, height: -2 },
      elevation: 16,
    },
    collapsedBar: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingHorizontal: theme.spacing?.md || 16,
      paddingVertical: theme.spacing?.sm || 12,
      minHeight: 72,
    },
    expandButton: {
      width: 44,
      height: 44,
      alignItems: 'center',
      justifyContent: 'center',
    },
    expandIcon: {
      fontSize: 24,
      color: theme.colors.text,
    },
    skipButton: {
      width: 44,
      height: 44,
      alignItems: 'center',
      justifyContent: 'center',
    },
    skipCircle: {
      width: 40,
      height: 40,
      borderRadius: 20,
      borderWidth: 2,
      borderColor: theme.colors.text,
      alignItems: 'center',
      justifyContent: 'center',
    },
    skipText: {
      fontSize: 12,
      fontWeight: '600',
      color: theme.colors.text,
    },
    playButton: {
      width: 56,
      height: 56,
      alignItems: 'center',
      justifyContent: 'center',
    },
    playCircle: {
      width: 56,
      height: 56,
      borderRadius: 28,
      alignItems: 'center',
      justifyContent: 'center',
    },
    playIcon: {
      fontSize: 20,
      color: theme.colors.surface,
      fontWeight: 'bold',
    },
    artworkContainer: {
      width: 48,
      height: 48,
      borderRadius: 8,
      overflow: 'hidden',
    },
    expandedContent: {
      maxHeight: 400,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border,
    },
    expandedInner: {
      padding: theme.spacing?.lg || 20,
    },
    title: {
      marginBottom: theme.spacing?.md || 16,
      fontWeight: '600',
    },
    timeRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: theme.spacing?.xs || 8,
    },
    progressContainer: {
      height: 32,
      marginBottom: theme.spacing?.lg || 20,
      justifyContent: 'center',
    },
    progressTrack: {
      height: 4,
      backgroundColor: theme.colors.border,
      borderRadius: 2,
      overflow: 'hidden',
    },
    progressFill: {
      height: '100%',
      borderRadius: 2,
    },
    progressTouchable: {
      position: 'absolute',
      left: 0,
      right: 0,
      top: 0,
      bottom: 0,
    },
    speedSection: {
      marginBottom: theme.spacing?.lg || 20,
    },
    sectionLabel: {
      marginBottom: theme.spacing?.md || 12,
      textTransform: 'uppercase',
      fontWeight: '600',
    },
    speedMarkers: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: theme.spacing?.xs || 4,
      paddingHorizontal: 16, // Match half the thumb width (32px / 2)
    },
    speedMarker: {
      fontSize: 14,
      fontWeight: '400',
      color: theme.colors.text,
    },
    speedMarkerMain: {
      fontSize: 16,
      fontWeight: '600',
      color: theme.colors.text,
    },
    speedMarkerMuted: {
      fontSize: 14,
      fontWeight: '300',
      color: theme.colors.textSecondary,
      opacity: 0.5,
    },
    speedSliderContainer: {
      height: 44,
      justifyContent: 'center',
      marginBottom: theme.spacing?.sm || 8,
      marginHorizontal: 16, // Inset to align with markers
    },
    speedSliderTrack: {
      height: 6,
      backgroundColor: theme.colors.border,
      borderRadius: 3,
      overflow: 'hidden',
    },
    speedSliderFill: {
      height: '100%',
      borderRadius: 3,
    },
    speedSliderTouchable: {
      position: 'absolute',
      left: 0,
      right: 0,
      top: 0,
      bottom: 0,
      justifyContent: 'center',
    },
    speedSliderThumb: {
      position: 'absolute',
      width: 32,
      height: 32,
      borderRadius: 16,
      backgroundColor: theme.colors.surface,
      shadowColor: theme.colors.text,
      shadowOpacity: 0.3,
      shadowRadius: 4,
      shadowOffset: { width: 0, height: 2 },
      elevation: 4,
      borderWidth: 1,
      borderColor: theme.colors.border,
      transform: [{ translateX: -16 }], // Center the thumb on the position
    },
    speedSliderThumbActive: {
      transform: [{ translateX: -16 }, { scale: 1.2 }], // Keep centered while scaling
      shadowOpacity: 0.5,
      shadowRadius: 6,
      elevation: 8,
    },
    currentSpeedText: {
      textAlign: 'center',
      fontSize: 16,
      fontWeight: '600',
      color: theme.colors.text,
    },
    transcriptSection: {
      marginBottom: theme.spacing?.lg || 20,
    },
    transcriptText: {
      lineHeight: 22,
    },
  });
