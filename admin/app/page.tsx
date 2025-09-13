/**
 * Dashboard Overview Page
 *
 * Main dashboard page showing system overview and quick access to key features.
 */

import { DashboardOverview } from '@/modules/admin/components/dashboard/DashboardOverview';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Monitor and manage your learning platform
        </p>
      </div>

      <DashboardOverview />
    </div>
  );
}
