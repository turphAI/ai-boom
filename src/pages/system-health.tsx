import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { SystemHealth } from '@/components/dashboard/SystemHealth'

export default function SystemHealthPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Health Monitor</h1>
          <p className="text-gray-600 mt-1">Real-time monitoring of data sources, scrapers, and system performance</p>
        </div>

        {/* System Health Component */}
        <SystemHealth />
      </div>
    </DashboardLayout>
  )
}
