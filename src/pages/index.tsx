import React, { useState, useEffect } from 'react'
import Head from 'next/head'
import { useSession, signIn, signOut } from 'next-auth/react'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { MetricCard } from '@/components/dashboard/MetricCard'
import { MetricChart } from '@/components/dashboard/MetricChart'
import { SystemHealth } from '@/components/dashboard/SystemHealth'
import { AlertConfig } from '@/components/dashboard/AlertConfig'
import { 
  MetricData, 
  HistoricalData, 
  AlertConfig as AlertConfigType, 
  SystemHealth as SystemHealthType,
  Alert
} from '@/types/dashboard'
import { RefreshCw, Settings, Bell } from 'lucide-react'

export default function Dashboard() {
  const { data: session, status } = useSession()
  const [metrics, setMetrics] = useState<MetricData[]>([])
  const [historicalData, setHistoricalData] = useState<Record<string, HistoricalData[]>>({})
  const [alertConfigs, setAlertConfigs] = useState<AlertConfigType[]>([])
  const [systemHealth, setSystemHealth] = useState<SystemHealthType[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  useEffect(() => {
    if (session) {
      fetchDashboardData()
      // Set up auto-refresh every 30 seconds, but only if there are no errors
      const interval = setInterval(() => {
        if (!loading) {
          fetchDashboardData()
        }
      }, 30000)
      return () => clearInterval(interval)
    }
  }, [session, loading])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      
      // Fetch current metrics
      const metricsResponse = await fetch('/api/metrics/current')
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json()
        setMetrics(metricsData.metrics || [])
      } else {
        console.warn('Failed to fetch metrics:', metricsResponse.status)
        setMetrics([])
      }

      // Fetch historical data for charts
      const historicalResponse = await fetch('/api/metrics/historical?days=30')
      if (historicalResponse.ok) {
        const historicalData = await historicalResponse.json()
        setHistoricalData(historicalData.data || {})
      } else {
        console.warn('Failed to fetch historical data:', historicalResponse.status)
        setHistoricalData({})
      }

      // Fetch alert configurations
      const alertConfigResponse = await fetch('/api/alerts/config')
      if (alertConfigResponse.ok) {
        const alertConfigData = await alertConfigResponse.json()
        setAlertConfigs(alertConfigData.configs || [])
      } else {
        console.warn('Failed to fetch alert configs:', alertConfigResponse.status)
        setAlertConfigs([])
      }

      // Fetch system health
      const healthResponse = await fetch('/api/system/health')
      if (healthResponse.ok) {
        const healthData = await healthResponse.json()
        setSystemHealth(healthData.health || [])
      } else {
        console.warn('Failed to fetch system health:', healthResponse.status)
        setSystemHealth([])
      }

      setLastRefresh(new Date())
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      // Set empty defaults to prevent infinite retries
      setMetrics([])
      setHistoricalData({})
      setAlertConfigs([])
      setSystemHealth([])
    } finally {
      setLoading(false)
    }
  }

  const handleSaveAlertConfig = async (config: any) => {
    try {
      const response = await fetch('/api/alerts/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      if (response.ok) {
        fetchDashboardData()
      }
    } catch (error) {
      console.error('Failed to save alert config:', error)
    }
  }

  const handleUpdateAlertConfig = async (id: string, config: any) => {
    try {
      const response = await fetch(`/api/alerts/config/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      if (response.ok) {
        fetchDashboardData()
      }
    } catch (error) {
      console.error('Failed to update alert config:', error)
    }
  }

  const handleDeleteAlertConfig = async (id: string) => {
    try {
      const response = await fetch(`/api/alerts/config/${id}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        fetchDashboardData()
      }
    } catch (error) {
      console.error('Failed to delete alert config:', error)
    }
  }

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-[400px]">
          <CardHeader>
            <CardTitle className="text-center">Boom-Bust Sentinel</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-muted-foreground mb-4">
              Sign in to access the financial monitoring dashboard
            </p>
            <Button onClick={() => signIn()} className="w-full">
              Sign In
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <>
      <Head>
        <title>Boom-Bust Sentinel Dashboard</title>
        <meta name="description" content="Financial market monitoring dashboard" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <DashboardLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
              <p className="text-gray-600 mt-1">
                Last updated: {lastRefresh.toLocaleTimeString()}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchDashboardData}
                disabled={loading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button variant="outline" size="sm" onClick={() => signOut()}>
                Sign Out
              </Button>
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {metrics.map((metric) => (
              <MetricCard key={metric.key || metric.id || `metric-${metric.name}`} metric={metric} />
            ))}
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {Object.entries(historicalData).map(([key, data]) => (
              <MetricChart
                key={`chart-${key}`}
                title={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                data={data}
                dataKey="value"
                color="#3b82f6"
                unit={metrics.find(m => m.name.toLowerCase().includes(key.split('_')[0]))?.unit}
                type="area"
              />
            ))}
          </div>

          {/* System Health and Alert Config */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SystemHealth healthData={systemHealth} />
            <AlertConfig
              configs={alertConfigs}
              onSave={handleSaveAlertConfig}
              onUpdate={handleUpdateAlertConfig}
              onDelete={handleDeleteAlertConfig}
            />
          </div>
        </div>
      </DashboardLayout>
    </>
  )
}