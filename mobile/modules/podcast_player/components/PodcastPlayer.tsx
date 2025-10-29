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
  Event,
  useProgress,
  usePlaybackState,
  useTrackPlayerEvents,
} from 'react-native-track-player';
import {
  Text,
  ArtworkImage,
  uiSystemProvider,
  useHaptics,
  Slider,
} from '../../ui_system/public';
import { usePodcastPlayer } from '../hooks/usePodcastPlayer';
import { usePodcastState } from '../hooks/usePodcastState';
import type { PodcastTrack } from '../models';
import { PLAYBACK_SPEEDS, usePodcastStore } from '../store';

interface PodcastPlayerProps {
  readonly track: PodcastTrack;
  readonly unitId: string;
  readonly artworkUrl?: string;
  readonly defaultExpanded?: boolean;
}

export function PodcastPlayer({
  track,
  unitId,
  artworkUrl,
  defaultExpanded = false,
}: PodcastPlayerProps): React.ReactElement {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const haptics = useHaptics();
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const {
    playbackState,
    currentTrack,
    globalSpeed,
    playlist,
    autoplayEnabled,
  } = usePodcastState();
  const {
    loadTrack,
    play,
    pause,
    skipBackward,
    skipForward,
    skipToNext,
    skipToPrevious,
    seekTo,
    setSpeed,
    toggleAutoplay,
  } = usePodcastPlayer();

  const isCurrentTrack = currentTrack?.unitId === unitId;

  const [isSeekingPosition, setIsSeekingPosition] = useState(false);
  const [pendingSeekPosition, setPendingSeekPosition] = useState(0);

  const playlistLength = playlist?.tracks.length ?? 0;
  const currentPlaylistIndex = playlist?.currentTrackIndex ?? 0;
  const hasPlaylist = playlistLength > 0;
  const isPreviousDisabled = !hasPlaylist || currentPlaylistIndex <= 0;
  const isNextDisabled =
    !hasPlaylist || currentPlaylistIndex >= playlistLength - 1;

  const trackIndicatorText = useMemo(() => {
    if (!playlist || !currentTrack) {
      return null;
    }
    if (!currentTrack.lessonId) {
      return 'Intro';
    }

    const lessonTracks = playlist.tracks.filter(
      trackItem => trackItem.lessonId
    );
    const lessonIndex =
      typeof currentTrack.lessonIndex === 'number'
        ? currentTrack.lessonIndex
        : lessonTracks.findIndex(
            trackItem => trackItem.lessonId === currentTrack.lessonId
          );

    if (lessonIndex >= 0 && lessonTracks.length > 0) {
      return `Lesson ${lessonIndex + 1} of ${lessonTracks.length}`;
    }

    return currentTrack.title;
  }, [playlist, currentTrack]);

  // Speed slider drag state
  const sliderWidth = useRef(0);
  const sliderX = useRef(0);
  const [isDraggingSpeed, setIsDraggingSpeed] = useState(false);
  const [dragSpeedPosition, setDragSpeedPosition] = useState(0);
  const lastLoadedTrackIdRef = useRef<string | null>(null);

  // Load track when component mounts (same as FullPlayer)
  useEffect(() => {
    if (!track || isCurrentTrack) {
      return;
    }

    // Prevent duplicate loads of the same track
    const trackId = track.lessonId || `${track.unitId}:intro`;
    if (lastLoadedTrackIdRef.current === trackId) {
      console.log('[PodcastPlayer] Track already loaded, skipping:', trackId);
      return;
    }

    lastLoadedTrackIdRef.current = trackId;
    loadTrack(track).catch(error => {
      console.warn('[PodcastPlayer] Failed to load track', error);
      lastLoadedTrackIdRef.current = null; // Reset on error to allow retry
    });
  }, [isCurrentTrack, loadTrack, track]);

  // Use built-in hooks from react-native-track-player for real-time updates
  const trackProgress = useProgress(1000); // Poll every 1 second
  const trackPlaybackState = usePlaybackState();

  // Sync TrackPlayer progress to our store
  useEffect(() => {
    if (!isCurrentTrack) {
      return;
    }

    console.log('[PodcastPlayer] 📊 Progress from useProgress hook:', {
      position: trackProgress.position.toFixed(1),
      duration: trackProgress.duration,
      buffered: trackProgress.buffered,
    });

    const store = usePodcastStore.getState();
    const fallbackDuration = track.durationSeconds ?? 0;
    const duration =
      trackProgress.duration > 0 ? trackProgress.duration : fallbackDuration;

    store.updatePlaybackState({
      position: trackProgress.position,
      buffered: trackProgress.buffered,
      duration,
    });
  }, [
    trackProgress.position,
    trackProgress.duration,
    trackProgress.buffered,
    isCurrentTrack,
    track.durationSeconds,
  ]);

  // Sync TrackPlayer playback state to our store
  useEffect(() => {
    if (!isCurrentTrack) {
      return;
    }

    console.log(
      '[PodcastPlayer] 🎵 State from usePlaybackState hook:',
      trackPlaybackState
    );

    const isPlaying = trackPlaybackState.state === 'playing';
    const isLoading =
      trackPlaybackState.state === 'buffering' ||
      trackPlaybackState.state === 'loading';

    usePodcastStore.getState().updatePlaybackState({
      isPlaying,
      isLoading,
    });
  }, [trackPlaybackState, isCurrentTrack]);

  // Listen for errors
  useTrackPlayerEvents([Event.PlaybackError], async event => {
    if (event.type === Event.PlaybackError) {
      console.error('[PodcastPlayer] 🚨 Playback error:', event);
    }
  });

  const isPlaying = playbackState.isPlaying;
  const position = playbackState.position ?? 0;
  const duration = playbackState.duration || track.durationSeconds;
  const sliderMaximum = Math.max(duration || 0, track.durationSeconds);
  const displayedPosition = isSeekingPosition ? pendingSeekPosition : position;

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

  const formatTime = (seconds: number | null | undefined): string => {
    if (!Number.isFinite(seconds)) {
      return '0:00';
    }
    const safeSeconds = Math.max(0, seconds ?? 0);
    const mins = Math.floor(safeSeconds / 60);
    const secs = Math.floor(safeSeconds % 60)
      .toString()
      .padStart(2, '0');
    return `${mins}:${secs}`;
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

  const handlePreviousTrack = (): void => {
    if (isPreviousDisabled) {
      return;
    }
    haptics.trigger('light');
    skipToPrevious().catch(() => {});
  };

  const handleNextTrack = (): void => {
    if (isNextDisabled) {
      return;
    }
    haptics.trigger('light');
    skipToNext().catch(() => {});
  };

  const handleToggleAutoplay = (): void => {
    haptics.trigger('light');
    toggleAutoplay();
  };

  const handleToggleExpand = (): void => {
    haptics.trigger('medium');
    setIsExpanded(!isExpanded);
  };

  const clampSeekPosition = useCallback(
    (value: number): number => {
      if (!Number.isFinite(value)) {
        return 0;
      }
      const max = sliderMaximum > 0 ? sliderMaximum : 0;
      return Math.min(Math.max(value, 0), max);
    },
    [sliderMaximum]
  );

  const handleSeekStart = useCallback(
    (value: number): void => {
      setIsSeekingPosition(true);
      setPendingSeekPosition(clampSeekPosition(value));
      haptics.trigger('light');
    },
    [clampSeekPosition, haptics]
  );

  const handleSeekChange = useCallback(
    (value: number): void => {
      setPendingSeekPosition(clampSeekPosition(value));
    },
    [clampSeekPosition]
  );

  const handleSeekComplete = useCallback(
    (value: number): void => {
      const nextValue = clampSeekPosition(value);
      setPendingSeekPosition(nextValue);
      setIsSeekingPosition(false);
      haptics.trigger('medium');
      seekTo(nextValue).catch(() => {});
    },
    [clampSeekPosition, haptics, seekTo]
  );

  useEffect(() => {
    if (!isSeekingPosition && Number.isFinite(position)) {
      setPendingSeekPosition(clampSeekPosition(position));
    }
  }, [clampSeekPosition, isSeekingPosition, position]);

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
        <Pressable
          onPress={handleToggleExpand}
          style={styles.expandButton}
          accessibilityLabel={isExpanded ? 'Collapse player' : 'Expand player'}
          accessibilityRole="button"
          testID="podcast-expand-toggle"
        >
          <Text variant="h2" style={styles.expandIcon}>
            {isExpanded ? '⌄' : '⌃'}
          </Text>
        </Pressable>

        <Pressable
          onPress={handlePreviousTrack}
          style={[
            styles.trackSkipButton,
            isPreviousDisabled && styles.trackSkipButtonDisabled,
          ]}
          accessibilityLabel="Previous podcast"
          accessibilityRole="button"
          disabled={isPreviousDisabled}
          testID="podcast-prev-track"
        >
          <View style={styles.trackSkipCircle}>
            <Text variant="caption" style={styles.trackSkipIcon}>
              ⏮
            </Text>
          </View>
        </Pressable>

        <Pressable
          onPress={handleTogglePlay}
          style={styles.playButton}
          accessibilityLabel={isPlaying ? 'Pause' : 'Play'}
          accessibilityRole="button"
          testID="podcast-play-toggle"
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

        <Pressable
          onPress={handleNextTrack}
          style={[
            styles.trackSkipButton,
            isNextDisabled && styles.trackSkipButtonDisabled,
          ]}
          accessibilityLabel="Next podcast"
          accessibilityRole="button"
          disabled={isNextDisabled}
          testID="podcast-next-track"
        >
          <View style={styles.trackSkipCircle}>
            <Text variant="caption" style={styles.trackSkipIcon}>
              ⏭
            </Text>
          </View>
        </Pressable>

        <View style={styles.trackSummary}>
          {trackIndicatorText ? (
            <Text
              variant="caption"
              style={styles.trackIndicatorCollapsed}
              testID="podcast-track-indicator"
            >
              {trackIndicatorText}
            </Text>
          ) : null}
          <Text
            variant="body"
            numberOfLines={1}
            style={styles.trackTitleCollapsed}
            accessibilityLabel={`Now playing ${track.title}`}
          >
            {track.title}
          </Text>
        </View>

        <View style={styles.artworkContainer}>
          <ArtworkImage
            title={track.title}
            imageUrl={artworkUrl}
            variant="thumbnail"
            style={styles.artwork}
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

            {trackIndicatorText ? (
              <Text variant="caption" style={styles.trackIndicatorExpanded}>
                {trackIndicatorText}
              </Text>
            ) : null}

            {/* Time Labels */}
            <View style={styles.timeRow}>
              <Text variant="caption" color={theme.colors.textSecondary}>
                {formatTime(displayedPosition)}
              </Text>
              <Text variant="caption" color={theme.colors.textSecondary}>
                {formatTime(sliderMaximum)}
              </Text>
            </View>

            <Slider
              value={displayedPosition}
              minimumValue={0}
              maximumValue={sliderMaximum > 0 ? sliderMaximum : 0}
              step={0.1}
              onSlidingStart={handleSeekStart}
              onValueChange={handleSeekChange}
              onSlidingComplete={handleSeekComplete}
              disabled={sliderMaximum <= 0}
              containerStyle={styles.sliderContainer}
              showValueLabels={false}
              testID="podcast-player-slider"
            />

            <View style={styles.secondaryControls}>
              <Pressable
                onPress={handleSkipBackward}
                style={styles.secondaryControlButton}
                accessibilityLabel="Rewind 15 seconds"
                accessibilityRole="button"
                testID="podcast-rewind-15"
              >
                <Text style={styles.secondaryControlText}>−15s</Text>
              </Pressable>
              <Pressable
                onPress={handleSkipForward}
                style={styles.secondaryControlButton}
                accessibilityLabel="Forward 15 seconds"
                accessibilityRole="button"
                testID="podcast-forward-15"
              >
                <Text style={styles.secondaryControlText}>+15s</Text>
              </Pressable>
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

            <View style={styles.autoplaySection}>
              <Text
                variant="caption"
                color={theme.colors.textSecondary}
                style={styles.sectionLabel}
              >
                Autoplay
              </Text>
              <Pressable
                onPress={handleToggleAutoplay}
                style={styles.autoplayToggle}
                accessibilityLabel="Toggle autoplay"
                accessibilityRole="button"
                testID="podcast-autoplay-toggle"
              >
                <View
                  style={[
                    styles.autoplayToggleIndicator,
                    autoplayEnabled && styles.autoplayToggleIndicatorActive,
                  ]}
                >
                  <Text
                    style={[
                      styles.autoplayToggleText,
                      autoplayEnabled && styles.autoplayToggleTextActive,
                    ]}
                  >
                    {autoplayEnabled ? 'On' : 'Off'}
                  </Text>
                </View>
              </Pressable>
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
      paddingBottom: theme.spacing?.md || 16,
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
    trackSkipButton: {
      width: 44,
      height: 44,
      alignItems: 'center',
      justifyContent: 'center',
      marginHorizontal: 4,
    },
    trackSkipButtonDisabled: {
      opacity: 0.4,
    },
    trackSkipCircle: {
      width: 40,
      height: 40,
      borderRadius: 20,
      borderWidth: 2,
      borderColor: theme.colors.text,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: theme.colors.surface,
    },
    trackSkipIcon: {
      fontSize: 14,
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
      borderRadius: 4,
      overflow: 'hidden',
    },
    artwork: {
      width: 48,
      height: 48,
      borderRadius: 4,
    },
    trackSummary: {
      flex: 1,
      marginHorizontal: theme.spacing?.sm || 8,
      justifyContent: 'center',
    },
    trackIndicatorCollapsed: {
      color: theme.colors.textSecondary,
      marginBottom: 2,
      textTransform: 'uppercase',
      fontSize: 12,
      fontWeight: '600',
    },
    trackTitleCollapsed: {
      color: theme.colors.text,
      fontWeight: '600',
      fontSize: 14,
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
    trackIndicatorExpanded: {
      marginBottom: theme.spacing?.sm || 8,
      color: theme.colors.textSecondary,
      textTransform: 'uppercase',
      fontWeight: '600',
    },
    timeRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: theme.spacing?.xs || 8,
    },
    sliderContainer: {
      marginBottom: theme.spacing?.lg || 20,
    },
    secondaryControls: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: theme.spacing?.md || 16,
    },
    secondaryControlButton: {
      flex: 1,
      marginHorizontal: 8,
      paddingVertical: 12,
      borderRadius: 24,
      borderWidth: 1,
      borderColor: theme.colors.border,
      backgroundColor: theme.colors.surface,
      alignItems: 'center',
      justifyContent: 'center',
    },
    secondaryControlText: {
      fontWeight: '600',
      color: theme.colors.text,
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
    autoplaySection: {
      marginBottom: theme.spacing?.lg || 20,
    },
    autoplayToggle: {
      alignSelf: 'flex-start',
    },
    autoplayToggleIndicator: {
      paddingHorizontal: 16,
      paddingVertical: 8,
      borderRadius: 20,
      borderWidth: 1,
      borderColor: theme.colors.border,
      backgroundColor: theme.colors.surface,
    },
    autoplayToggleIndicatorActive: {
      backgroundColor: theme.colors.primary,
      borderColor: theme.colors.primary,
    },
    autoplayToggleText: {
      fontWeight: '600',
      color: theme.colors.text,
    },
    autoplayToggleTextActive: {
      color: theme.colors.surface,
    },
    transcriptSection: {
      marginBottom: theme.spacing?.lg || 20,
    },
    transcriptText: {
      lineHeight: 22,
    },
  });
