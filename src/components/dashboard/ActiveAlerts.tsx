import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { AlertTriangle, XCircle, Bell, Clock } from 'lucide-react'

interface ActiveAlert {
  id: string
  type: string
  dataSource: string
  metricName: string
  message: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  timestamp: string
  acknowledged: boolean
}

interface ActiveAlertsProps {
  alerts: ActiveAlert[]
  onAcknowledge: (id: string) => void
  onDismiss: (id: string) => void
}

export function ActiveAlerts({ alerts, onAcknowledge, onDismiss }: ActiveAlertsProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  const activeAlerts = alerts.filter(alert => !alert.acknowledged)
  const criticalAlerts = activeAlerts.filter(alert => alert.severity === 'critical')
  const warningAlerts = activeAlerts.filter(alert => alert.severity === 'medium' || alert.severity === 'high')
  
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
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) {
      return 'Just now'
    } else if (diffInMinutes < 60) {
      return `${diffInMinutes}m ago`
    } else {
      const diffInHours = Math.floor(diffInMinutes / 60)
      return `${diffInHours}h ago`
    }
  }

  if (activeAlerts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Bell className="h-5 w-5 text-green-500" />
            <span>Active Alerts</span>
            <Badge variant="outline" className="text-green-600">
              All Clear
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4 text-muted-foreground">
            <p>No active alerts</p>
            <p className="text-sm">All metrics are within normal ranges</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={criticalAlerts.length > 0 ? 'border-red-200 bg-red-50' : 'border-yellow-200 bg-yellow-50'}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {criticalAlerts.length > 0 ? (
              <XCircle className="h-5 w-5 text-red-500" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
            )}
            <span>Active Alerts</span>
            <Badge variant={criticalAlerts.length > 0 ? 'destructive' : 'default'}>
              {activeAlerts.length} Active
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'Collapse' : 'Expand'}
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Critical Alerts */}
          {criticalAlerts.length > 0 && (
            <div>
              <h4 className="font-medium text-sm text-red-700 mb-2">Critical Alerts</h4>
              <div className="space-y-2">
                {criticalAlerts.slice(0, isExpanded ? undefined : 2).map((alert) => (
                  <div key={alert.id} className="p-3 rounded-lg border border-red-200 bg-red-100">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {getSeverityIcon(alert.severity)}
                        <div className="flex-1">
                          <div className="font-medium text-sm text-red-900">{alert.metricName}</div>
                          <div className="text-xs text-red-700 mt-1 whitespace-pre-line">
                            {alert.message}
                          </div>
                          <div className="text-xs text-red-600 mt-1">
                            {formatTimestamp(alert.timestamp)} • {alert.dataSource}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant="destructive" className="text-xs">
                          {alert.severity}
                        </Badge>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onAcknowledge(alert.id)}
                        >
                          Acknowledge
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Warning Alerts */}
          {warningAlerts.length > 0 && (
            <div>
              <h4 className="font-medium text-sm text-yellow-700 mb-2">Warning Alerts</h4>
              <div className="space-y-2">
                {warningAlerts.slice(0, isExpanded ? undefined : 2).map((alert) => (
                  <div key={alert.id} className="p-3 rounded-lg border border-yellow-200 bg-yellow-100">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {getSeverityIcon(alert.severity)}
                        <div className="flex-1">
                          <div className="font-medium text-sm text-yellow-900">{alert.metricName}</div>
                          <div className="text-xs text-yellow-700 mt-1 whitespace-pre-line">
                            {alert.message}
                          </div>
                          <div className="text-xs text-yellow-600 mt-1">
                            {formatTimestamp(alert.timestamp)} • {alert.dataSource}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant="secondary" className="text-xs">
                          {alert.severity}
                        </Badge>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onAcknowledge(alert.id)}
                        >
                          Acknowledge
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Show more/less button */}
          {activeAlerts.length > 4 && (
            <div className="text-center pt-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(!isExpanded)}
              >
                {isExpanded ? 'Show Less' : `Show ${activeAlerts.length - 4} More`}
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
