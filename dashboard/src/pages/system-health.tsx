import { useState, useEffect } from 'react'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { SystemHealth } from '@/components/dashboard/SystemHealth'
import { SystemHealth as SystemHealthType } from '@/types/dashboard'

export default function SystemHealthPage() {
  const [healthData, setHealthData] = useState<SystemHealthType[]>([])

  useEffect(() => {
    // Mock health data for now
    setHealthData([
      {
        dataSource: 'bond_issuance',
        status: 'healthy',
        lastUpdate: new Date().toISOString(),
        uptime: 86400,
      },
      {
        dataSource: 'bdc_discount',
        status: 'healthy',
        lastUpdate: new Date().toISOString(),
        uptime: 86400,
      },
      {
        dataSource: 'credit_fund',
        status: 'degraded',
        lastUpdate: new Date(Date.now() - 3600000).toISOString(),
        uptime: 82800,
        errorMessage: 'Data source temporarily unavailable',
      },
      {
        dataSource: 'bank_provision',
        status: 'failed',
        lastUpdate: new Date(Date.now() - 7200000).toISOString(),
        uptime: 79200,
        errorMessage: 'Connection timeout',
      },
    ])
  }, [])

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Health Monitor</h1>
          <p className="text-gray-600 mt-1">Real-time monitoring of data sources, scrapers, and system performance</p>
        </div>

        <SystemHealth healthData={healthData} />
      </div>
    </DashboardLayout>
  )
}
