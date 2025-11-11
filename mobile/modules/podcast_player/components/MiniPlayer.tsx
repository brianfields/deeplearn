import React, { useMemo, useState, useEffect, useCallback } from 'react';
import {
  View,
  StyleSheet,
  Pressable,
  ActivityIndicator,
  Modal,
  SafeAreaView,
  ScrollView,
  Switch,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  Event,
  useProgress,
  useTrackPlayerEvents,
} from 'react-native-track-player';
import {
  Text,
  ArtworkImage,
  uiSystemProvider,
  useHaptics,
  Slider,
} from '../../ui_system/public';
import { reducedMotion } from '../../ui_system/utils/motion';
import { RotateCcw, RotateCw } from 'lucide-react-native';
import { usePodcastPlayer } from '../hooks/usePodcastPlayer';
import { usePodcastState } from '../hooks/usePodcastState';
import { usePodcastStore } from '../store';
import { catalogProvider } from '../../catalog/public';
import type { PodcastTrack } from '../models';

/**
 * MiniPlayer Component
 *
 * A compact, fixed-position player that appears at the bottom of the screen
 * when a podcast is playing or paused. Shows playback controls and basic info.
 * Tapping on it expands to show the full player.
 *
 * Renders nothing when in 'idle' state (no podcast has been played yet).
 */
export function MiniPlayer(): React.ReactElement {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const insets = useSafeAreaInsets();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const haptics = useHaptics();
  const [isExpanded, setIsExpanded] = useState(false);

  // Seeking state
  const [isSeekingPosition, setIsSeekingPosition] = useState(false);
  const [pendingSeekPosition, setPendingSeekPosition] = useState(0);

  const {
    currentTrack,
    playbackUIState,
    playlist,
    autoplayEnabled,
    globalSpeed,
    playbackState,
  } = usePodcastState();
  const {
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

  // Use TrackPlayer's useProgress hook for real-time position updates
  const trackProgress = useProgress(1000);

  // Sync TrackPlayer progress to our store
  useEffect(() => {
    if (!currentTrack) {
      return;
    }

    const store = usePodcastStore.getState();
    const fallbackDuration = currentTrack.durationSeconds ?? 0;
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
    currentTrack,
  ]);

  // Listen for playback errors
  useTrackPlayerEvents([Event.PlaybackError], async event => {
    if (event.type === Event.PlaybackError) {
      console.error('[MiniPlayer] 🚨 Playback error:', event);
    }
  });

  // Fetch transcript for current track if it's missing
  useEffect(() => {
    const lessonId = currentTrack?.lessonId;
    const hasTranscript = currentTrack?.transcript !== null;

    if (!lessonId || hasTranscript) {
      return;
    }

    const fetchTranscript = async (): Promise<void> => {
      try {
        const catalog = catalogProvider();
        const lessonDetail = await catalog.getLessonDetail(lessonId);
        if (!lessonDetail) {
          console.log(
            '[MiniPlayer] Could not fetch lesson detail for transcript'
          );
          return;
        }

        // Update the currentTrack in the store with the fetched transcript
        const track = usePodcastStore.getState().currentTrack;
        if (!track) {
          return;
        }

        const updatedTrack: PodcastTrack = {
          ...track,
          transcript: lessonDetail.podcastTranscript ?? null,
        };
        usePodcastStore.getState().setCurrentTrack(updatedTrack);
      } catch (error) {
        console.warn('[MiniPlayer] Failed to fetch transcript:', error);
      }
    };

    void fetchTranscript();
  }, [currentTrack?.lessonId, currentTrack?.transcript]);

  const isPlaying = playbackState.isPlaying;
  const isLoading = playbackState.isLoading;
  const position = playbackState.position ?? 0;
  const duration =
    playbackState.duration || (currentTrack?.durationSeconds ?? 0);
  const displayedPosition = isSeekingPosition ? pendingSeekPosition : position;

  const playlistLength = playlist?.tracks.length ?? 0;
  const currentPlaylistIndex = playlist?.currentTrackIndex ?? 0;
  const hasPlaylist = playlistLength > 0;
  // Previous button is never disabled if we have a playlist - it either seeks to 0 or goes to previous track
  const isPreviousDisabled = !hasPlaylist;
  const isNextDisabled =
    !hasPlaylist || currentPlaylistIndex >= playlistLength - 1;

  const handleTogglePlay = (): void => {
    haptics.trigger('light');
    if (isPlaying) {
      pause().catch(() => {});
    } else {
      play().catch(() => {});
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

  const handleExpand = (): void => {
    haptics.trigger('medium');
    setIsExpanded(true);
  };

  const handleCollapse = (): void => {
    haptics.trigger('medium');
    setIsExpanded(false);
  };

  const handlePreviousTrack = (): void => {
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

  const handleIncreaseSpeed = (): void => {
    const newSpeed = Math.min(3.0, Math.round((globalSpeed + 0.1) * 10) / 10);
    if (newSpeed !== globalSpeed) {
      haptics.trigger('light');
      setSpeed(newSpeed as any).catch(() => {});
    }
  };

  const handleDecreaseSpeed = (): void => {
    const newSpeed = Math.max(0.5, Math.round((globalSpeed - 0.1) * 10) / 10);
    if (newSpeed !== globalSpeed) {
      haptics.trigger('light');
      setSpeed(newSpeed as any).catch(() => {});
    }
  };

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

  const clampSeekPosition = useCallback(
    (value: number): number => {
      if (!Number.isFinite(value)) {
        return 0;
      }
      const max = duration > 0 ? duration : 0;
      return Math.min(Math.max(value, 0), max);
    },
    [duration]
  );

  const handleSeekStart = (value: number): void => {
    setIsSeekingPosition(true);
    setPendingSeekPosition(clampSeekPosition(value));
    haptics.trigger('light');
  };

  const handleSeekChange = (value: number): void => {
    setPendingSeekPosition(clampSeekPosition(value));
  };

  const handleSeekComplete = (value: number): void => {
    const nextValue = clampSeekPosition(value);
    setPendingSeekPosition(nextValue);
    setIsSeekingPosition(false);
    haptics.trigger('medium');
    seekTo(nextValue).catch(() => {});
  };

  // Sync pending seek position with actual position when not seeking
  useEffect(() => {
    if (!isSeekingPosition && Number.isFinite(position)) {
      setPendingSeekPosition(clampSeekPosition(position));
    }
  }, [isSeekingPosition, position, duration, clampSeekPosition]);

  const displayTitle = useMemo(() => {
    if (!currentTrack?.lessonId) {
      return 'Intro Podcast';
    }
    return currentTrack.title || 'Lesson Podcast';
  }, [currentTrack]);

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

  // Don't render anything if in idle state or no track
  if (playbackUIState === 'idle' || !currentTrack) {
    return <View />;
  }

  return (
    <>
      {/* Mini Player Bar */}
      <Pressable
        onPress={handleExpand}
        style={[
          styles.container,
          { paddingBottom: Math.max(16, insets.bottom) },
        ]}
      >
        <View style={styles.innerContainer}>
          {/* Artwork thumbnail */}
          <View style={styles.artworkContainer}>
            <ArtworkImage
              title={displayTitle}
              imageUrl={currentTrack.artworkUrl || undefined}
              variant="thumbnail"
              style={styles.artwork}
            />
          </View>

          {/* Title and info */}
          <View style={styles.infoContainer}>
            <Text variant="body" numberOfLines={1} style={styles.title}>
              {displayTitle}
            </Text>
            <Text
              variant="caption"
              color={theme.colors.textSecondary}
              numberOfLines={1}
            >
              {playbackState.isPlaying ? 'Playing' : 'Paused'}
            </Text>
          </View>

          {/* Control buttons */}
          <View style={styles.controlsContainer}>
            <Pressable
              onPress={e => {
                e.stopPropagation();
                handleSkipBackward();
              }}
              style={styles.controlButton}
              accessibilityLabel="Rewind 30 seconds"
              accessibilityRole="button"
              testID="mini-player-rewind"
            >
              <RotateCcw
                size={18}
                color={theme.colors.primary}
                strokeWidth={2}
              />
            </Pressable>

            <Pressable
              onPress={e => {
                e.stopPropagation();
                handleTogglePlay();
              }}
              style={[
                styles.playButton,
                { backgroundColor: theme.colors.primary },
              ]}
              accessibilityLabel={isPlaying ? 'Pause' : 'Play'}
              accessibilityRole="button"
              disabled={isLoading}
              testID="mini-player-play-toggle"
            >
              {isLoading ? (
                <ActivityIndicator color="white" size="small" />
              ) : (
                <Text style={styles.playIcon}>{isPlaying ? '❚❚' : '▶'}</Text>
              )}
            </Pressable>

            <Pressable
              onPress={e => {
                e.stopPropagation();
                handleSkipForward();
              }}
              style={styles.controlButton}
              accessibilityLabel="Forward 30 seconds"
              accessibilityRole="button"
              testID="mini-player-forward"
            >
              <RotateCw
                size={18}
                color={theme.colors.primary}
                strokeWidth={2}
              />
            </Pressable>
          </View>
        </View>
      </Pressable>

      {/* Expanded Player Modal */}
      <Modal
        animationType={reducedMotion.enabled ? 'none' : 'slide'}
        visible={isExpanded}
        presentationStyle="pageSheet"
        onRequestClose={handleCollapse}
        testID="mini-player-expanded-modal"
      >
        <SafeAreaView
          style={[
            styles.modalContainer,
            { backgroundColor: theme.colors.background },
          ]}
        >
          <View style={styles.modalHeader}>
            <Pressable
              onPress={handleCollapse}
              style={styles.modalCloseButton}
              accessibilityLabel="Close player"
              accessibilityRole="button"
              testID="mini-player-modal-close"
            >
              <Text variant="h2" style={styles.modalCloseIcon}>
                ⌄
              </Text>
            </Pressable>
            <View style={styles.modalHeaderContent}>
              {trackIndicatorText ? (
                <Text
                  variant="caption"
                  style={[
                    styles.modalTrackIndicator,
                    { color: theme.colors.textSecondary },
                  ]}
                >
                  {trackIndicatorText}
                </Text>
              ) : null}
              <Text
                variant="h2"
                style={[styles.modalTitle, { color: theme.colors.text }]}
              >
                {currentTrack?.title || 'Podcast'}
              </Text>
            </View>
          </View>

          <ScrollView
            style={styles.expandedContent}
            showsVerticalScrollIndicator={false}
          >
            <View style={styles.expandedInner}>
              {/* Time Labels */}
              <View style={styles.timeRow}>
                <Text variant="caption" color={theme.colors.textSecondary}>
                  {formatTime(displayedPosition)}
                </Text>
                <Text
                  variant="body"
                  color={theme.colors.text}
                  style={styles.timeRemaining}
                >
                  {formatTime(duration - displayedPosition)} left ({globalSpeed}
                  ×)
                </Text>
                <Text variant="caption" color={theme.colors.textSecondary}>
                  -{formatTime(duration)}
                </Text>
              </View>

              <Slider
                value={displayedPosition}
                minimumValue={0}
                maximumValue={duration > 0 ? duration : 0}
                step={0.1}
                onSlidingStart={handleSeekStart}
                onValueChange={handleSeekChange}
                onSlidingComplete={handleSeekComplete}
                disabled={duration <= 0}
                containerStyle={styles.sliderContainer}
                showValueLabels={false}
                testID="mini-player-slider"
              />

              {/* Compact control layout */}
              <View style={styles.compactControls}>
                <Pressable
                  onPress={handlePreviousTrack}
                  style={[
                    styles.compactControlButton,
                    isPreviousDisabled && styles.compactControlButtonDisabled,
                  ]}
                  accessibilityLabel="Previous lesson"
                  accessibilityRole="button"
                  disabled={isPreviousDisabled}
                  testID="mini-player-prev-track-expanded"
                >
                  <Text
                    variant="h2"
                    style={[
                      styles.compactControlIcon,
                      {
                        color: isPreviousDisabled
                          ? theme.colors.textSecondary
                          : theme.colors.text,
                      },
                    ]}
                  >
                    ⏮
                  </Text>
                </Pressable>

                <Pressable
                  onPress={handleSkipBackward}
                  style={styles.compactControlButton}
                  accessibilityLabel="Rewind 30 seconds"
                  accessibilityRole="button"
                  testID="mini-player-rewind-30-expanded"
                >
                  <View style={styles.skipIconContainer}>
                    <RotateCcw
                      size={44}
                      color={theme.colors.text}
                      strokeWidth={2}
                    />
                    <Text
                      variant="caption"
                      style={styles.skipSecondsInsideExpanded}
                    >
                      30
                    </Text>
                  </View>
                </Pressable>

                <Pressable
                  onPress={handleTogglePlay}
                  style={styles.compactPlayButton}
                  accessibilityLabel={isPlaying ? 'Pause' : 'Play'}
                  accessibilityRole="button"
                  testID="mini-player-play-toggle-expanded"
                >
                  <View
                    style={[
                      styles.compactPlayCircle,
                      { backgroundColor: theme.colors.primary },
                    ]}
                  >
                    <Text variant="h1" style={styles.compactPlayIcon}>
                      {isPlaying ? '❚❚' : '▶'}
                    </Text>
                  </View>
                </Pressable>

                <Pressable
                  onPress={handleSkipForward}
                  style={styles.compactControlButton}
                  accessibilityLabel="Forward 30 seconds"
                  accessibilityRole="button"
                  testID="mini-player-forward-30-expanded"
                >
                  <View style={styles.skipIconContainer}>
                    <RotateCw
                      size={44}
                      color={theme.colors.text}
                      strokeWidth={2}
                    />
                    <Text
                      variant="caption"
                      style={styles.skipSecondsInsideExpanded}
                    >
                      30
                    </Text>
                  </View>
                </Pressable>

                <Pressable
                  onPress={handleNextTrack}
                  style={[
                    styles.compactControlButton,
                    isNextDisabled && styles.compactControlButtonDisabled,
                  ]}
                  accessibilityLabel="Next lesson"
                  accessibilityRole="button"
                  disabled={isNextDisabled}
                  testID="mini-player-next-track-expanded"
                >
                  <Text
                    variant="h2"
                    style={[
                      styles.compactControlIcon,
                      {
                        color: isNextDisabled
                          ? theme.colors.textSecondary
                          : theme.colors.text,
                      },
                    ]}
                  >
                    ⏭
                  </Text>
                </Pressable>
              </View>

              {/* Playback speed controls */}
              <View style={styles.speedContainer}>
                <Text
                  variant="body"
                  color={theme.colors.text}
                  style={styles.speedLabel}
                >
                  Playback Speed
                </Text>
                <View style={styles.speedButtons}>
                  <Pressable
                    onPress={handleDecreaseSpeed}
                    style={styles.speedButton}
                    accessibilityLabel="Decrease speed"
                    accessibilityRole="button"
                  >
                    <Text variant="body" color={theme.colors.primary}>
                      -
                    </Text>
                  </Pressable>
                  <Text
                    variant="body"
                    color={theme.colors.text}
                    style={styles.speedValue}
                  >
                    {globalSpeed.toFixed(2)}×
                  </Text>
                  <Pressable
                    onPress={handleIncreaseSpeed}
                    style={styles.speedButton}
                    accessibilityLabel="Increase speed"
                    accessibilityRole="button"
                  >
                    <Text variant="body" color={theme.colors.primary}>
                      +
                    </Text>
                  </Pressable>
                </View>
              </View>

              {/* Autoplay toggle */}
              <View style={styles.autoplayContainer}>
                <Text variant="body" color={theme.colors.text}>
                  Autoplay next lesson
                </Text>
                <Switch
                  value={autoplayEnabled}
                  onValueChange={handleToggleAutoplay}
                />
              </View>

              {/* Transcript */}
              <View style={styles.transcriptSection}>
                <Text
                  variant="caption"
                  color={theme.colors.textSecondary}
                  style={styles.sectionLabel}
                >
                  Transcript
                </Text>
                {currentTrack?.transcript ? (
                  <Text
                    variant="body"
                    color={theme.colors.text}
                    style={styles.transcriptText}
                  >
                    {currentTrack.transcript}
                  </Text>
                ) : (
                  <Text
                    variant="body"
                    color={theme.colors.textSecondary}
                    style={styles.transcriptUnavailable}
                  >
                    Transcript not available for this podcast
                  </Text>
                )}
              </View>
            </View>
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </>
  );
}

const createStyles = (theme: any) =>
  StyleSheet.create({
    container: {
      position: 'absolute',
      bottom: 0,
      left: 0,
      right: 0,
      backgroundColor: theme.colors.surface,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border,
      paddingHorizontal: 20,
      paddingBottom: 16,
      paddingTop: 12,
    },
    innerContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      height: 60,
    },
    artworkContainer: {
      marginRight: 12,
    },
    artwork: {
      width: 48,
      height: 48,
      borderRadius: 4,
    },
    infoContainer: {
      flex: 1,
      marginRight: 12,
    },
    title: {
      marginBottom: 2,
    },
    controlsContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
    controlButton: {
      width: 32,
      height: 32,
      justifyContent: 'center',
      alignItems: 'center',
    },
    playButton: {
      width: 40,
      height: 40,
      borderRadius: 20,
      justifyContent: 'center',
      alignItems: 'center',
    },
    playIcon: {
      fontSize: 16,
      color: 'white',
      fontWeight: 'bold',
    },
    // Expanded modal styles
    modalContainer: {
      flex: 1,
    },
    modalHeader: {
      paddingHorizontal: 16,
      paddingTop: 8,
      paddingBottom: 16,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
    },
    modalCloseButton: {
      alignSelf: 'flex-start',
      padding: 8,
      marginLeft: -8,
    },
    modalCloseIcon: {
      fontSize: 32,
      color: theme.colors.text,
    },
    modalHeaderContent: {
      marginTop: 8,
    },
    modalTrackIndicator: {
      fontSize: 12,
      textTransform: 'uppercase',
      letterSpacing: 1,
      marginBottom: 4,
    },
    modalTitle: {
      fontSize: 24,
      fontWeight: '600',
    },
    expandedContent: {
      flex: 1,
    },
    expandedInner: {
      padding: 16,
      gap: 24,
    },
    timeRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    timeRemaining: {
      textAlign: 'center',
    },
    sliderContainer: {
      marginVertical: 8,
    },
    compactControls: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 16,
      paddingVertical: 16,
    },
    compactControlButton: {
      width: 48,
      height: 48,
      justifyContent: 'center',
      alignItems: 'center',
    },
    compactControlButtonDisabled: {
      opacity: 0.3,
    },
    compactControlIcon: {
      fontSize: 32,
    },
    skipIconContainer: {
      position: 'relative',
      width: 44,
      height: 44,
      justifyContent: 'center',
      alignItems: 'center',
    },
    skipSecondsInsideExpanded: {
      position: 'absolute',
      fontSize: 12,
      fontWeight: '600',
      color: theme.colors.text,
    },
    compactPlayButton: {
      width: 72,
      height: 72,
      justifyContent: 'center',
      alignItems: 'center',
    },
    compactPlayCircle: {
      width: 72,
      height: 72,
      borderRadius: 36,
      justifyContent: 'center',
      alignItems: 'center',
    },
    compactPlayIcon: {
      fontSize: 28,
      color: 'white',
      fontWeight: 'bold',
    },
    speedContainer: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingVertical: 12,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border,
    },
    speedLabel: {
      fontSize: 16,
    },
    speedButtons: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 16,
    },
    speedButton: {
      width: 36,
      height: 36,
      justifyContent: 'center',
      alignItems: 'center',
      borderWidth: 1,
      borderColor: theme.colors.border,
      borderRadius: 18,
    },
    speedValue: {
      fontSize: 16,
      minWidth: 60,
      textAlign: 'center',
    },
    autoplayContainer: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingVertical: 12,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border,
    },
    transcriptSection: {
      paddingTop: 16,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border,
    },
    sectionLabel: {
      fontSize: 12,
      textTransform: 'uppercase',
      letterSpacing: 1,
      marginBottom: 8,
    },
    transcriptText: {
      fontSize: 15,
      lineHeight: 24,
    },
    transcriptUnavailable: {
      fontSize: 15,
      fontStyle: 'italic',
    },
  });
