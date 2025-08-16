import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert } from '@/types/dashboard'
import { Bell, CheckCircle, Clock, AlertTriangle, XCircle } from 'lucide-react'

interface AlertHistoryProps {
  alerts: Alert[]
  onAcknowledge: (id: string) => void
  onDismiss: (id: string) => void
}

export function AlertHistory({ alerts, onAcknowledge, onDismiss }: AlertHistoryProps) {
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'high':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />
      case 'medium':
        return <Bell className="h-4 w-4 text-yellow-500" />
      case 'low':
        return <Clock className="h-4 w-4 text-blue-500" />
      default:
        return <Bell className="h-4 w-4 text-gray-500" />
    }
  }

  const getSeverityVariant = (severity: string) => {
    switch (severity) {
      case 'critical': return 'destructive'
      case 'high': return 'default'
      case 'medium': return 'secondary'
      case 'low': return 'outline'
      default: return 'secondary'
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
    
    if (diffInHours < 1) {
      return 'Just now'
    } else if (diffInHours < 24) {
      return `${diffInHours}h ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  const unacknowledgedAlerts = alerts.filter(alert => !alert.acknowledged)
  const acknowledgedAlerts = alerts.filter(alert => alert.acknowledged)

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-lg">Alert History</CardTitle>
        <Badge variant="outline">
          {unacknowledgedAlerts.length} active
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Active Alerts */}
          {unacknowledgedAlerts.length > 0 && (
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-2">Active Alerts</h4>
              <div className="space-y-2">
                {unacknowledgedAlerts.slice(0, 5).map((alert) => (
                  <div key={alert.id} className="flex items-center justify-between p-3 rounded-lg border border-red-200 bg-red-50">
                    <div className="flex items-center space-x-3">
                      {getSeverityIcon(alert.severity)}
                      <div>
                        <div className="font-medium text-sm">{alert.metricName}</div>
                        <div className="text-xs text-muted-foreground">{alert.message}</div>
                        <div className="text-xs text-muted-foreground">
                          {formatTimestamp(alert.timestamp)} • {alert.dataSource}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant={getSeverityVariant(alert.severity)}>
                        {alert.severity}
                      </Badge>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onAcknowledge(alert.id)}
                      >
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Acknowledge
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Acknowledged Alerts */}
          {acknowledgedAlerts.length > 0 && (
            <div>
              <h4 className="font-medium text-sm text-muted-foreground mb-2">Recent Alerts</h4>
              <div className="space-y-2">
                {acknowledgedAlerts.slice(0, 3).map((alert) => (
                  <div key={alert.id} className="flex items-center justify-between p-2 rounded-lg border">
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <div>
                        <div className="font-medium text-sm">{alert.metricName}</div>
                        <div className="text-xs text-muted-foreground">{alert.message}</div>
                        <div className="text-xs text-muted-foreground">
                          {formatTimestamp(alert.timestamp)} • {alert.dataSource}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline" className="text-xs">
                        {alert.severity}
                      </Badge>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onDismiss(alert.id)}
                      >
                        Dismiss
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {alerts.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No alerts triggered yet</p>
              <p className="text-xs">Alerts will appear here when thresholds are breached</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
