import React from 'react';
import { ActivityIndicator, View } from 'react-native';
import { Download } from 'lucide-react-native';
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
}: Props): React.ReactElement {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();
  const { trigger } = useHaptics();

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

  const handleDownload = (): void => {
    if (!onDownload || !canDownload) {
      return;
    }
    onDownload(unit.id);
  };

  const downloadButtonTestId =
    index !== undefined ? `download-button-${index}` : undefined;

  return (
    <Box
      testID={index !== undefined ? `unit-card-${index}` : undefined}
      mb="sm"
    >
      <Card
        variant="default"
        onPress={handlePress}
        disabled={isDisabled}
        style={[
          unit.status === 'failed'
            ? { borderLeftWidth: 4, borderLeftColor: theme.colors.error }
            : null,
        ]}
      >
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'flex-start',
            columnGap: ui.getSpacing('md'),
          }}
        >
          <ArtworkImage
            title={unit.title}
            imageUrl={unit.artImageUrl ?? undefined}
            description={unit.artImageDescription ?? undefined}
            variant="thumbnail"
            style={{ flexShrink: 0 }}
            testID={index !== undefined ? `unit-art-${index}` : undefined}
          />

          <View style={{ flex: 1 }}>
            <View
              style={{
                flexDirection: 'row',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                marginBottom: ui.getSpacing('sm'),
              }}
            >
              <Text
                variant="title"
                weight="700"
                color={
                  isDisabled ? theme.colors.textSecondary : theme.colors.text
                }
                style={{ flex: 1, marginRight: ui.getSpacing('sm') }}
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
                />
              </View>
            )}

            {showFailedActions && (
              <View
                style={{
                  flexDirection: 'row',
                  justifyContent: 'flex-end',
                  marginTop: ui.getSpacing('sm'),
                  marginBottom: ui.getSpacing('xs'),
                  columnGap: ui.getSpacing('sm'),
                }}
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
                      index !== undefined
                        ? `dismiss-button-${index}`
                        : undefined
                    }
                  />
                )}
              </View>
            )}

            {showDownloadStatusInfo && downloadStatusText && (
              <View
                style={{
                  flexDirection: 'row',
                  alignItems: 'center',
                  columnGap: ui.getSpacing('xs'),
                  marginBottom: downloadStatusSpacing,
                }}
              >
                {isDownloadInProgress && (
                  <ActivityIndicator
                    size="small"
                    color={theme.colors.primary}
                  />
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
                  { alignSelf: 'flex-start' },
                  !showDownloadStatusInfo
                    ? { marginTop: ui.getSpacing('sm') }
                    : null,
                ]}
                testID={downloadButtonTestId}
              />
            )}

            <View
              style={{
                flexDirection: 'row',
                justifyContent: 'space-between',
                marginTop: metadataMarginTop,
              }}
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
