import { useState, useEffect } from 'react'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { SystemHealth } from '@/components/dashboard/SystemHealth'
import { SystemHealth as SystemHealthType } from '@/types/dashboard'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { RefreshCw, Calendar, Clock, Info } from 'lucide-react'

interface ScheduleData {
  name: string;
  displayName: string;
  cronExpression: string;
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  description: string;
  timezone: string;
  nextRunDescription: string;
  humanReadableSchedule: string;
}

export default function SystemHealthPage() {
  const [healthData, setHealthData] = useState<SystemHealthType[]>([])
  const [schedules, setSchedules] = useState<ScheduleData[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  useEffect(() => {
    fetchSystemHealth()
    fetchSchedules()
  }, [])

  const fetchSchedules = async () => {
    try {
      const response = await fetch('/api/system/schedules')
      const data = await response.json()
      if (data.success) {
        setSchedules(data.schedules)
      }
    } catch (error) {
      console.error('Error fetching schedules:', error)
    }
  }

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
          status: item.status === 'healthy' ? 'healthy' : item.status === 'failed' ? 'failed' : 'degraded',
          lastUpdate: item.lastCheck,
          uptime: item.uptime || 86400, // Default to 24 hours if not provided
          errorMessage: item.errorMessage || (item.status !== 'healthy' ? item.details : undefined),
          fallbackInfo: item.fallbackInfo,
          metadata: item.metadata
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

        {/* Scraper Schedule Table */}
        <Card className="mt-6">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <div className="flex items-center space-x-2">
              <Calendar className="h-5 w-5 text-muted-foreground" />
              <CardTitle className="text-lg">Scraper Schedules</CardTitle>
            </div>
            <Badge variant="outline" className="text-xs">
              All times in UTC
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Scraper</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Frequency</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Schedule</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Next Run</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {schedules.map((schedule) => (
                    <tr key={schedule.name} className="border-b last:border-0 hover:bg-muted/50 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-medium">{schedule.displayName}</div>
                        <div className="text-xs text-muted-foreground font-mono">{schedule.name}</div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge 
                          variant={
                            schedule.frequency === 'daily' ? 'default' :
                            schedule.frequency === 'weekly' ? 'secondary' :
                            schedule.frequency === 'monthly' ? 'outline' :
                            'outline'
                          }
                          className={
                            schedule.frequency === 'quarterly' ? 'border-purple-300 text-purple-700 bg-purple-50' : ''
                          }
                        >
                          {schedule.frequency.charAt(0).toUpperCase() + schedule.frequency.slice(1)}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm">{schedule.humanReadableSchedule}</span>
                        </div>
                        <div className="text-xs text-muted-foreground font-mono mt-1">
                          {schedule.cronExpression}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`text-sm font-medium ${
                          schedule.nextRunDescription === 'Today' ? 'text-green-600' :
                          schedule.nextRunDescription === 'Tomorrow' ? 'text-blue-600' :
                          'text-muted-foreground'
                        }`}>
                          {schedule.nextRunDescription}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-start space-x-1 max-w-xs">
                          <Info className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                          <span className="text-sm text-muted-foreground">{schedule.description}</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {schedules.length === 0 && !loading && (
              <div className="text-center py-8 text-muted-foreground">
                <Calendar className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No schedule data available</p>
              </div>
            )}
            <div className="mt-4 pt-4 border-t text-xs text-muted-foreground">
              <p className="flex items-center space-x-1">
                <Info className="h-3 w-3" />
                <span>
                  Schedules are configured in <code className="bg-muted px-1 py-0.5 rounded">serverless.yml</code> and 
                  executed via AWS CloudWatch Events. Update <code className="bg-muted px-1 py-0.5 rounded">src/lib/schedules.ts</code> to 
                  keep this table in sync with any schedule changes.
                </span>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
