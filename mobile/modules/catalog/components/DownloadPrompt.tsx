import React, { useMemo } from 'react';
import { ActivityIndicator, View, StyleSheet } from 'react-native';
import type { DownloadStatus } from '../../offline_cache/public';
import {
  Card,
  Text,
  Box,
  Button,
  uiSystemProvider,
} from '../../ui_system/public';
import { layoutStyles } from '../../ui_system/styles/layout';

interface DownloadPromptProps {
  readonly title: string;
  readonly description?: string | null;
  readonly lessonCount: number;
  readonly estimatedSizeBytes?: number | null;
  readonly downloadStatus: DownloadStatus;
  readonly downloadedAssets?: number;
  readonly assetCount?: number;
  readonly onDownload?: () => void;
  readonly onCancel?: () => void;
  readonly isDownloadActionPending?: boolean;
  readonly isCancelPending?: boolean;
}

export function DownloadPrompt({
  title,
  description,
  lessonCount,
  estimatedSizeBytes,
  downloadStatus,
  downloadedAssets,
  assetCount,
  onDownload,
  onCancel,
  isDownloadActionPending,
  isCancelPending,
}: DownloadPromptProps): React.ReactElement {
  const ui = uiSystemProvider();
  const theme = ui.getCurrentTheme();

  const { statusLabel, color: statusColor } = useMemo(() => {
    switch (downloadStatus) {
      case 'pending':
        return {
          statusLabel: 'Download queued...',
          color: theme.colors.primary,
        };
      case 'in_progress': {
        if (typeof assetCount === 'number' && assetCount > 0) {
          const completed = Math.min(downloadedAssets ?? 0, assetCount);
          return {
            statusLabel: `Downloading... ${completed}/${assetCount} assets`,
            color: theme.colors.primary,
          };
        }
        return {
          statusLabel: 'Downloading assets...',
          color: theme.colors.primary,
        };
      }
      case 'failed':
        return {
          statusLabel: 'Download failed. Please try again.',
          color: theme.colors.error,
        };
      default:
        return { statusLabel: null, color: theme.colors.textSecondary };
    }
  }, [
    assetCount,
    downloadStatus,
    downloadedAssets,
    theme.colors.error,
    theme.colors.primary,
    theme.colors.textSecondary,
  ]);

  const formattedSize = useMemo(() => {
    if (!estimatedSizeBytes || estimatedSizeBytes <= 0) {
      return 'Unknown size';
    }
    return formatBytes(estimatedSizeBytes);
  }, [estimatedSizeBytes]);

  const isInProgress =
    downloadStatus === 'pending' || downloadStatus === 'in_progress';
  const isFailed = downloadStatus === 'failed';

  return (
    <Card
      variant="default"
      style={[
        localStyles.card,
        { padding: ui.getSpacing('lg'), gap: ui.getSpacing('lg') },
      ]}
      testID="download-prompt"
    >
      <Box style={{ gap: ui.getSpacing('sm') }}>
        <Text variant="h2" style={layoutStyles.fontWeightSemibold}>
          Download required
        </Text>
        <Text variant="body" color={theme.colors.textSecondary}>
          {title}
        </Text>
        {description ? (
          <Text variant="secondary" color={theme.colors.textSecondary}>
            {description}
          </Text>
        ) : null}
        <Text variant="secondary" color={theme.colors.textSecondary}>
          {lessonCount > 0
            ? `${lessonCount} lesson${lessonCount === 1 ? '' : 's'}`
            : 'Lesson count unavailable'}
        </Text>
      </Box>

      <Box style={{ gap: ui.getSpacing('xs') }}>
        <Text variant="body" weight="600">
          Estimated download size
        </Text>
        <Text variant="secondary" color={theme.colors.textSecondary}>
          {formattedSize}
        </Text>
      </Box>

      {statusLabel ? (
        <Box style={[layoutStyles.row, { gap: ui.getSpacing('sm') }]}>
          {isInProgress ? (
            <ActivityIndicator size="small" color={statusColor} />
          ) : null}
          <Text variant="secondary" color={statusColor}>
            {statusLabel}
          </Text>
        </Box>
      ) : null}

      <View style={[layoutStyles.column, { gap: ui.getSpacing('sm') }]}>
        <Button
          title={isFailed ? 'Retry download' : 'Download unit'}
          onPress={() => onDownload?.()}
          loading={isDownloadActionPending}
          disabled={isInProgress}
          fullWidth
          variant="primary"
          size="large"
          testID="download-prompt-primary"
        />
        <Button
          title={isInProgress ? 'Cancel download' : 'Cancel'}
          onPress={() => onCancel?.()}
          loading={isCancelPending}
          variant={isInProgress ? 'secondary' : 'tertiary'}
          size="large"
          fullWidth
          testID="download-prompt-secondary"
        />
      </View>
    </Card>
  );
}

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return 'Unknown size';
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

const localStyles = StyleSheet.create({
  card: {
    margin: 0,
  },
});
