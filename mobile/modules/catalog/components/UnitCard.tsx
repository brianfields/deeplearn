import React from 'react';
import {
  ActivityIndicator,
  Alert,
  TouchableOpacity,
  View,
  StyleSheet,
} from 'react-native';
import { Download, Trash2 } from 'lucide-react-native';
import { Swipeable } from 'react-native-gesture-handler';
import type { Unit } from '../../content/public';
import type { DownloadStatus } from '../../offline_cache/public';
import { UnitProgressIndicator } from './UnitProgressIndicator';
import {
  Card,
  Text,
  Box,
  Button,
  ArtworkImage,
  uiSystemProvider,
  useHaptics,
} from '../../ui_system/public';
import { layoutStyles } from '../../ui_system/styles/layout';

interface Props {
  unit: Unit;
  onPress: (u: Unit) => void;
  onRetry?: (unitId: string) => void;
  onDismiss?: (unitId: string) => void;
  index?: number;
  downloadStatus?: DownloadStatus;
  downloadedAssets?: number;
  assetCount?: number;
  storageBytes?: number;
  onDownload?: (unitId: string) => void;
  isDownloadActionPending?: boolean;
  canRemoveFromMyUnits?: boolean;
  onRemoveFromMyUnits?: (unit: Unit) => void;
  isRemoveActionPending?: boolean;
}

export function UnitCard({
  unit,
  onPress,
  onRetry,
  onDismiss,
  index,
  downloadStatus,
  downloadedAssets,
  assetCount,
  storageBytes,
  onDownload,
  isDownloadActionPending,
  canRemoveFromMyUnits = false,
  onRemoveFromMyUnits,
  isRemoveActionPending = false,
}: Props): React.ReactElement {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const { trigger } = useHaptics();
  const swipeableRef = React.useRef<Swipeable | null>(null);

  // Check if unit has been creating for too long (1 hour = 3600 seconds)
  const isStaleCreation = React.useMemo(() => {
    if (unit.status !== 'in_progress' || !unit.updatedAt) {
      return false;
    }
    try {
      const updatedTime = new Date(unit.updatedAt).getTime();
      const now = Date.now();
      const elapsedSeconds = (now - updatedTime) / 1000;
      return elapsedSeconds > 3600; // 1 hour timeout
    } catch {
      return false;
    }
  }, [unit.status, unit.updatedAt]);

  const isDisabled = !unit.isInteractive;
  const showFailedActions: boolean =
    unit.status === 'failed' && !!(onRetry || onDismiss);
  const isInteractive = unit.isInteractive;

  const resolvedDownloadStatus: DownloadStatus =
    downloadStatus ??
    (unit.downloadStatus as DownloadStatus | undefined) ??
    'idle';
  const isDownloaded = resolvedDownloadStatus === 'completed';
  const isDownloadInProgress =
    resolvedDownloadStatus === 'pending' ||
    resolvedDownloadStatus === 'in_progress';
  const isDownloadFailed = resolvedDownloadStatus === 'failed';
  const canDownload = isInteractive;
  const showDownloadButton =
    Boolean(onDownload) &&
    canDownload &&
    !isDownloaded &&
    !isDownloadInProgress;
  const showDownloadStatusInfo =
    isInteractive && (isDownloaded || isDownloadInProgress || isDownloadFailed);

  let downloadStatusText: string | null = null;
  let downloadStatusColor = theme.colors.textSecondary;

  if (isDownloadInProgress) {
    const total = assetCount ?? 0;
    const completed = downloadedAssets ?? 0;
    downloadStatusColor = theme.colors.primary;
    if (resolvedDownloadStatus === 'pending') {
      downloadStatusText = 'Download queued...';
    } else if (total > 0) {
      const clampedCompleted = Math.min(completed, total);
      downloadStatusText = `Downloading... ${clampedCompleted}/${total} assets`;
    } else {
      downloadStatusText = 'Downloading assets...';
    }
  } else if (isDownloadFailed) {
    downloadStatusText = 'Download failed. Try again.';
    downloadStatusColor = theme.colors.error;
  } else if (isDownloaded) {
    const bytes = storageBytes ?? 0;
    downloadStatusText =
      bytes > 0 ? `Downloaded • ${formatBytes(bytes)}` : 'Downloaded';
    downloadStatusColor = theme.colors.textSecondary;
  }

  const downloadStatusSpacing = ui.getSpacing(showDownloadButton ? 'xs' : 'sm');
  const metadataMarginTop =
    showDownloadStatusInfo || showDownloadButton ? ui.getSpacing('sm') : 0;

  const handlePress = (): void => {
    if (isDisabled) return;
    trigger('light');
    onPress(unit);
  };

  const handleRetry = (): void => {
    if (!onRetry) return;
    trigger('medium');
    onRetry(unit.id);
  };

  const handleDismiss = (): void => {
    if (!onDismiss) return;
    trigger('light');
    onDismiss(unit.id);
  };

  const closeSwipe = (): void => {
    swipeableRef.current?.close();
  };

  const handleRemoveFromMyUnits = (): void => {
    if (!onRemoveFromMyUnits || isRemoveActionPending) {
      return;
    }
    Alert.alert(
      'Remove from My Units',
      `Remove "${unit.title}" from My Units?`,
      [
        {
          text: 'Cancel',
          style: 'cancel',
          onPress: closeSwipe,
        },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () => {
            trigger('medium');
            onRemoveFromMyUnits(unit);
            closeSwipe();
          },
        },
      ]
    );
  };

  const renderRemoveAction = (): React.ReactElement => (
    <TouchableOpacity
      onPress={handleRemoveFromMyUnits}
      style={[styles.removeAction, { backgroundColor: theme.colors.error }]}
      disabled={isRemoveActionPending}
      testID={
        index !== undefined ? `unit-remove-swipe-${index}` : 'unit-remove-swipe'
      }
    >
      <Trash2 size={20} color={theme.colors.surface} />
      <Text variant="caption" color={theme.colors.surface}>
        Remove
      </Text>
    </TouchableOpacity>
  );

  const handleDownload = (): void => {
    if (!onDownload || !canDownload) {
      return;
    }
    onDownload(unit.id);
  };

  const downloadButtonTestId =
    index !== undefined ? `download-button-${index}` : undefined;

  const cardContent = (
    <Card
      variant="default"
      onPress={handlePress}
      disabled={isDisabled}
      style={[
        unit.status === 'failed'
          ? {
              borderLeftColor: theme.colors.error,
              ...styles.borderLeftError,
            }
          : null,
      ]}
    >
      <View style={[layoutStyles.rowStart, { columnGap: ui.getSpacing('md') }]}>
        <ArtworkImage
          title={unit.title}
          imageUrl={unit.artImageUrl ?? undefined}
          description={unit.artImageDescription ?? undefined}
          variant="thumbnail"
          style={layoutStyles.flexShrink0}
          testID={index !== undefined ? `unit-art-${index}` : undefined}
        />

        <View style={layoutStyles.flex1}>
          <View
            style={[
              layoutStyles.rowBetweenStart,
              { marginBottom: ui.getSpacing('sm') },
            ]}
          >
            <Text
              variant="title"
              weight="700"
              color={
                isDisabled ? theme.colors.textSecondary : theme.colors.text
              }
              style={[layoutStyles.flex1, { marginRight: ui.getSpacing('sm') }]}
              numberOfLines={2}
            >
              {unit.title}
            </Text>
          </View>

          <Text
            variant="secondary"
            color={isDisabled ? theme.colors.textSecondary : undefined}
            numberOfLines={2}
            style={{ marginBottom: ui.getSpacing('sm') }}
          >
            {unit.description || unit.progressMessage}
          </Text>

          {unit.status !== 'completed' && (
            <View style={{ marginBottom: ui.getSpacing('sm') }}>
              <UnitProgressIndicator
                status={unit.status}
                progress={unit.creationProgress}
                errorMessage={unit.errorMessage}
                isStale={isStaleCreation}
              />
            </View>
          )}

          {showFailedActions && (
            <View
              style={[
                layoutStyles.rowEnd,
                {
                  marginTop: ui.getSpacing('sm'),
                  marginBottom: ui.getSpacing('xs'),
                  columnGap: ui.getSpacing('sm'),
                },
              ]}
            >
              {onRetry && (
                <Button
                  title="Retry"
                  variant="primary"
                  size="small"
                  onPress={handleRetry}
                  testID={
                    index !== undefined ? `retry-button-${index}` : undefined
                  }
                />
              )}
              {onDismiss && (
                <Button
                  title="Dismiss"
                  variant="secondary"
                  size="small"
                  onPress={handleDismiss}
                  testID={
                    index !== undefined ? `dismiss-button-${index}` : undefined
                  }
                />
              )}
            </View>
          )}

          {showDownloadStatusInfo && downloadStatusText && (
            <View
              style={[
                layoutStyles.row,
                {
                  columnGap: ui.getSpacing('xs'),
                  marginBottom: downloadStatusSpacing,
                },
              ]}
            >
              {isDownloadInProgress && (
                <ActivityIndicator size="small" color={theme.colors.primary} />
              )}
              <Text variant="caption" color={downloadStatusColor}>
                {downloadStatusText}
              </Text>
            </View>
          )}

          {showDownloadButton && (
            <Button
              title={isDownloadFailed ? 'Retry download' : 'Download'}
              variant="primary"
              size="small"
              onPress={handleDownload}
              loading={isDownloadActionPending}
              icon={<Download size={16} color={theme.colors.surface} />}
              style={[
                layoutStyles.selfStart,
                !showDownloadStatusInfo
                  ? { marginTop: ui.getSpacing('sm') }
                  : null,
              ]}
              testID={downloadButtonTestId}
            />
          )}

          <View
            style={[layoutStyles.rowBetween, { marginTop: metadataMarginTop }]}
          >
            <Text
              variant="caption"
              color={isDisabled ? theme.colors.textSecondary : undefined}
            >
              {unit.targetLessonCount} lessons
            </Text>
          </View>
        </View>
      </View>
    </Card>
  );

  return (
    <Box
      testID={index !== undefined ? `unit-card-${index}` : undefined}
      mb="sm"
    >
      {canRemoveFromMyUnits && onRemoveFromMyUnits ? (
        <Swipeable
          ref={swipeableRef}
          friction={2}
          rightThreshold={40}
          renderRightActions={renderRemoveAction}
        >
          {cardContent}
        </Swipeable>
      ) : (
        cardContent
      )}
    </Box>
  );
}

function formatBytes(bytes: number): string {
  if (!bytes || bytes <= 0) {
    return '0 B';
  }
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  const precision = value < 10 && unitIndex > 0 ? 1 : 0;
  return `${value.toFixed(precision)} ${units[unitIndex]}`;
}

const styles = StyleSheet.create({
  removeAction: {
    width: 80, // ui.getSpacing('xl') * 2 ≈ 40 * 2 = 80
    justifyContent: 'center' as const,
    alignItems: 'center' as const,
  },
  borderLeftError: {
    borderLeftWidth: 4,
  },
});
