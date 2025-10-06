import { useState, useEffect } from 'react'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { SystemHealth } from '@/components/dashboard/SystemHealth'
import { SystemHealth as SystemHealthType } from '@/types/dashboard'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'

export default function SystemHealthPage() {
  const [healthData, setHealthData] = useState<SystemHealthType[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  useEffect(() => {
    fetchSystemHealth()
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(fetchSystemHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchSystemHealth = async (isManual = false) => {
    try {
      if (isManual) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }
      
      const response = await fetch('/api/system/health')
      const data = await response.json()
      
      if (data.success) {
        // Transform API data to match component interface
        const transformedData = data.health.map((item: any) => ({
          dataSource: item.component,
          status: item.status,
          lastUpdate: item.lastCheck,
          uptime: item.uptime || 86400, // Default to 24 hours if not provided
          errorMessage: item.errorMessage || (item.status !== 'healthy' ? item.details : undefined)
        }))
        setHealthData(transformedData)
        setLastRefresh(new Date())
      } else {
        console.error('Failed to fetch system health:', data.error)
      }
    } catch (error) {
      console.error('Error fetching system health:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    fetchSystemHealth(true)
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">System Health Monitor</h1>
            <p className="text-gray-600 mt-1">
              Real-time monitoring of data sources, scrapers, and system performance
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Last updated: {lastRefresh.toLocaleString()}
            </p>
          </div>
          <Button 
            onClick={handleRefresh} 
            disabled={refreshing || loading}
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </Button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : (
          <SystemHealth healthData={healthData} />
        )}
      </div>
    </DashboardLayout>
  )
}
