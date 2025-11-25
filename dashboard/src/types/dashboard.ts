export interface MetricData {
  id: string
  name: string
  value: number
  unit: string
  change: number
  changePercent: number
  status: 'healthy' | 'warning' | 'critical' | 'stale'
  lastUpdated: string
  source: string
  sourceCount?: number
}

export interface HistoricalData {
  timestamp: string
  value: number
  metadata?: Record<string, any>
}

export interface AlertConfig {
  id: string
  metricName: string
  dataSource: string
  thresholdType: 'absolute' | 'percentage' | 'standard_deviation'
  thresholdValue: number
  comparisonPeriod: number
  enabled: boolean
  channels: string[]
}

export interface SystemHealth {
  dataSource: string
  status: 'healthy' | 'degraded' | 'failed'
  lastUpdate: string
  errorMessage?: string
  uptime: number
  fallbackInfo?: {
    type: 'fallback' | 'partial'
    message: string
    sources?: string[]
    reason?: string
  }
  metadata?: {
    dataQuality?: string
    source?: string
  }
}

export interface Alert {
  id: string
  type: string
  dataSource: string
  metricName: string
  message: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  timestamp: string
  acknowledged: boolean
}