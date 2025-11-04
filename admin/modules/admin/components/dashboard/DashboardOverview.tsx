/**
 * Dashboard Overview Component
 *
 * Main dashboard showing key metrics for last 24 hours and 7 days.
 */

'use client';

import { useCallback, useEffect, useState } from 'react';
import { LoadingSpinner } from '../shared/LoadingSpinner';
import { ErrorMessage } from '../shared/ErrorMessage';
import { formatCost } from '@/lib/utils';

interface MetricValue {
  last_24h: number;
  last_7d: number;
}

interface MetricsData {
  signups: MetricValue;
  new_units: MetricValue;
  assistant_conversations: MetricValue;
  learning_sessions_started: MetricValue;
  learning_sessions_completed: MetricValue;
  llm_requests: MetricValue;
  llm_requests_cost: MetricValue;
}

interface DashboardOverviewProps {
  onRefetchChange?: (refetch: () => void) => void;
}

export function DashboardOverview({ onRefetchChange }: DashboardOverviewProps) {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/admin/dashboard-metrics');
      if (!response.ok) {
        throw new Error('Failed to fetch metrics');
      }
      const data = await response.json();
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load metrics');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  useEffect(() => {
    if (onRefetchChange) {
      onRefetchChange(fetchMetrics);
    }
  }, [fetchMetrics, onRefetchChange]);

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading dashboard..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load dashboard data."
        details={error}
      />
    );
  }

  if (!metrics) {
    return <div className="text-gray-500">No data available</div>;
  }

  const MetricCard = ({ title, value24h, value7d, formatter = (v: number) => v.toString() }: { title: string; value24h: number; value7d: number; formatter?: (v: number) => string }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-sm font-medium text-gray-600 mb-4">{title}</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-gray-500">Last 24h</p>
          <p className="text-2xl font-semibold text-gray-900">{formatter(value24h)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Last 7d</p>
          <p className="text-2xl font-semibold text-gray-900">{formatter(value7d)}</p>
        </div>
      </div>
    </div>
  );

  const DualMetricCard = ({
    title,
    value1_24h,
    value1_7d,
    value2_24h,
    value2_7d,
    formatter = (v: number) => v.toString()
  }: {
    title: string;
    value1_24h: number;
    value1_7d: number;
    value2_24h: number;
    value2_7d: number;
    formatter?: (v: number) => string
  }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-sm font-medium text-gray-600 mb-4">{title}</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-gray-500">Last 24h</p>
          <p className="text-2xl font-semibold text-gray-900">
            {formatter(value1_24h)} / {formatter(value2_24h)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Last 7d</p>
          <p className="text-2xl font-semibold text-gray-900">
            {formatter(value1_7d)} / {formatter(value2_7d)}
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Main Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <MetricCard
          title="Signups"
          value24h={metrics.signups.last_24h}
          value7d={metrics.signups.last_7d}
        />
        <MetricCard
          title="New Units"
          value24h={metrics.new_units.last_24h}
          value7d={metrics.new_units.last_7d}
        />
        <MetricCard
          title="Assistant Conversations"
          value24h={metrics.assistant_conversations.last_24h}
          value7d={metrics.assistant_conversations.last_7d}
        />
        <DualMetricCard
          title="Sessions Started / Completed"
          value1_24h={metrics.learning_sessions_started.last_24h}
          value1_7d={metrics.learning_sessions_started.last_7d}
          value2_24h={metrics.learning_sessions_completed.last_24h}
          value2_7d={metrics.learning_sessions_completed.last_7d}
        />
        <MetricCard
          title="LLM Requests"
          value24h={metrics.llm_requests.last_24h}
          value7d={metrics.llm_requests.last_7d}
        />
        <MetricCard
          title="LLM Requests Cost"
          value24h={metrics.llm_requests_cost.last_24h}
          value7d={metrics.llm_requests_cost.last_7d}
          formatter={formatCost}
        />
      </div>
    </div>
  );
}
