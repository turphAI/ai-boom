import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { MetricData } from '@/types/dashboard'
import { TrendingUp, TrendingDown, Clock } from 'lucide-react'

interface MetricCardProps {
  metric: MetricData
}

export function MetricCard({ metric }: MetricCardProps) {
  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'healthy': return 'success'
      case 'warning': return 'warning'
      case 'critical': return 'destructive'
      case 'stale': return 'stale'
      default: return 'secondary'
    }
  }

  const formatValue = (value: number, unit: string) => {
    if (unit === 'currency') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        notation: 'compact',
        maximumFractionDigits: 1
      }).format(value)
    }
    if (unit === 'percentage') {
      return `${value.toFixed(2)}%`
    }
    return `${value.toLocaleString()} ${unit}`
  }

  const isStale = metric.status === 'stale'
  const lastUpdated = new Date(metric.lastUpdated)
  const hoursAgo = Math.floor((Date.now() - lastUpdated.getTime()) / (1000 * 60 * 60))

  return (
    <Card className={`transition-all hover:shadow-md ${isStale ? 'opacity-75 border-orange-200' : ''}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{metric.name}</CardTitle>
        <Badge variant={getStatusVariant(metric.status)}>
          {metric.status}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {formatValue(metric.value, metric.unit)}
        </div>
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center text-xs text-muted-foreground">
            {metric.change !== 0 && (
              <>
                {metric.change > 0 ? (
                  <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
                ) : (
                  <TrendingDown className="h-3 w-3 mr-1 text-red-500" />
                )}
                <span className={metric.change > 0 ? 'text-green-500' : 'text-red-500'}>
                  {metric.changePercent > 0 ? '+' : ''}{metric.changePercent.toFixed(1)}%
                </span>
              </>
            )}
          </div>
          <div className="flex items-center text-xs text-muted-foreground">
            <Clock className="h-3 w-3 mr-1" />
            {isStale ? (
              <span className="text-orange-500">
                {hoursAgo}h ago
              </span>
            ) : (
              <span>
                {hoursAgo < 1 ? 'Just now' : `${hoursAgo}h ago`}
              </span>
            )}
          </div>
        </div>
        <div className="text-xs text-muted-foreground mt-1">
          Source: {metric.source}
        </div>
      </CardContent>
    </Card>
  )
}