/**
 * Dashboard Overview Page
 *
 * Main dashboard page showing system overview and quick access to key features.
 */

'use client';

import { useState } from 'react';
import { DashboardOverview } from '@/modules/admin/components/dashboard/DashboardOverview';
import { PageHeader } from '@/modules/admin/components/shared/PageHeader';

export default function DashboardPage() {
  const [refetchMetrics, setRefetchMetrics] = useState<(() => void) | null>(null);
  const [isReloading, setIsReloading] = useState(false);

  const handleReload = () => {
    if (refetchMetrics) {
      setIsReloading(true);
      refetchMetrics();
      // Reset loading state after a brief delay
      setTimeout(() => setIsReloading(false), 500);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Admin Dashboard"
        description="Monitor and manage your learning platform"
        onReload={handleReload}
        isReloading={isReloading}
      />

      <DashboardOverview onRefetchChange={setRefetchMetrics} />
    </div>
  );
}
