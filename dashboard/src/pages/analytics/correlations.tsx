import React, { useState, useEffect } from 'react'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { AlertTriangle, TrendingUp, TrendingDown, ArrowLeft, BarChart3, PieChart, Activity } from 'lucide-react'
import Link from 'next/link'
import { MetricData, HistoricalData } from '@/types/dashboard'
import { AnalyticsChart } from '@/components/analytics/AnalyticsChart'
import { DrillDownModal } from '@/components/analytics/DrillDownModal'
import { FilterPanel } from '@/components/analytics/FilterPanel'

interface CorrelationAnalytics {
  currentValue: number
  changePercent: number
  trend: 'up' | 'down' | 'stable'
  status: 'healthy' | 'warning' | 'critical'
  historicalData: HistoricalData[]
  breakdown: {
    byAssetClass: Array<{ asset: string; value: number; percentage: number }>
    byTimeframe: Array<{ timeframe: string; value: number; percentage: number }>
    byRegion: Array<{ region: string; value: number; percentage: number }>
  }
  insights: {
    keyTrends: string[]
    riskFactors: string[]
    recommendations: string[]
  }
}

export default function CorrelationAnalytics() {
  const [analytics, setAnalytics] = useState<CorrelationAnalytics | null>(null)
  const [historicalData, setHistoricalData] = useState<HistoricalData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [drillDownModal, setDrillDownModal] = useState<{
    isOpen: boolean
    title: string
    data: any[]
    dataKey: string
    color: string
    unit: string
    type: 'line' | 'area' | 'bar'
  }>({
    isOpen: false,
    title: '',
    data: [],
    dataKey: 'value',
    color: '#f59e0b',
    unit: '',
    type: 'line'
  })

  // Filter state
  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false)
  const [dateRange, setDateRange] = useState<{ start: Date; end: Date }>({
    start: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000), // 90 days ago
    end: new Date()
  })
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([])
  const [filteredHistoricalData, setFilteredHistoricalData] = useState<HistoricalData[]>([])

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch current metrics
      const metricsResponse = await fetch('/api/metrics/current')
      const metricsData = await metricsResponse.json()
      
      if (!metricsData.success) {
        throw new Error('Failed to fetch current metrics')
      }

      const correlationMetric = metricsData.metrics.find((m: any) => m.key === 'correlation')
      if (!correlationMetric) {
        throw new Error('Correlation metric not found')
      }

      // Fetch historical data
      const historicalResponse = await fetch('/api/metrics/historical?days=365')
      const historicalData = await historicalResponse.json()
      
      if (!historicalData.success) {
        throw new Error('Failed to fetch historical data')
      }

      const correlationHistoricalData = historicalData.data.correlation || []

      // Process analytics
      const analytics: CorrelationAnalytics = {
        currentValue: correlationMetric.value,
        changePercent: correlationMetric.changePercent,
        trend: correlationMetric.changePercent > 0.05 ? 'up' : correlationMetric.changePercent < -0.05 ? 'down' : 'stable',
        status: correlationMetric.status,
        historicalData: correlationHistoricalData,
        breakdown: {
          byAssetClass: [
            { asset: 'Equity-Equity', value: 0.85, percentage: 34.0 },
            { asset: 'Equity-Bond', value: -0.15, percentage: 6.0 },
            { asset: 'Bond-Bond', value: 0.65, percentage: 26.0 },
            { asset: 'Commodity-Equity', value: 0.25, percentage: 10.0 },
            { asset: 'Currency-Equity', value: -0.05, percentage: 2.0 },
            { asset: 'Others', value: 0.45, percentage: 18.0 }
          ],
          byTimeframe: [
            { timeframe: '1 Month', value: 0.72, percentage: 28.8 },
            { timeframe: '3 Months', value: 0.68, percentage: 27.2 },
            { timeframe: '6 Months', value: 0.65, percentage: 26.0 },
            { timeframe: '1 Year', value: 0.62, percentage: 24.8 }
          ],
          byRegion: [
            { region: 'US Markets', value: 0.78, percentage: 31.2 },
            { region: 'European Markets', value: 0.72, percentage: 28.8 },
            { region: 'Asian Markets', value: 0.68, percentage: 27.2 },
            { region: 'Emerging Markets', value: 0.32, percentage: 12.8 }
          ]
        },
        insights: {
          keyTrends: [
            'Cross-asset correlations increased 12% over the quarter',
            'Equity-bond correlation remains negative, providing diversification',
            'Regional correlations highest in developed markets',
            'Short-term correlations more volatile than long-term'
          ],
          riskFactors: [
            'Rising correlations may reduce portfolio diversification',
            'Central bank policy convergence driving correlation increases',
            'Global economic uncertainty affecting all asset classes',
            'Liquidity constraints during stress periods'
          ],
          recommendations: [
            'Monitor correlation trends for portfolio rebalancing',
            'Consider alternative assets for diversification',
            'Review hedge ratios in light of changing correlations',
            'Maintain geographic diversification strategies'
          ]
        }
      }

      setAnalytics(analytics)
      setHistoricalData(correlationHistoricalData)
      setFilteredHistoricalData(correlationHistoricalData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics')
    } finally {
      setLoading(false)
    }
  }

  const handleDrillDown = (title: string, data: any[], dataKey: string, color: string, unit: string, type: 'line' | 'area' | 'bar' = 'bar') => {
    setDrillDownModal({
      isOpen: true,
      title,
      data,
      dataKey,
      color,
      unit,
      type
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-100 text-green-800'
      case 'warning': return 'bg-yellow-100 text-yellow-800'
      case 'critical': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4 text-orange-500" />
      case 'down': return <TrendingDown className="h-4 w-4 text-green-500" />
      default: return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const getCorrelationColor = (value: number) => {
    if (value >= 0.7) return 'text-red-600'
    if (value >= 0.3) return 'text-orange-600'
    if (value >= -0.3) return 'text-yellow-600'
    return 'text-green-600'
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
        </div>
      </DashboardLayout>
    )
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Analytics</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={fetchAnalytics}>Retry</Button>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!analytics) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Data Available</h3>
            <p className="text-gray-600">Correlation analytics data is not available.</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link href="/analytics">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Analytics
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Correlation Analytics</h1>
              <p className="text-gray-600">Analysis of cross-asset correlation trends and diversification metrics</p>
            </div>
          </div>
          <Button onClick={() => setIsFilterPanelOpen(true)}>
            <BarChart3 className="h-4 w-4 mr-2" />
            Filters
          </Button>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Average Correlation</CardTitle>
              {getTrendIcon(analytics.trend)}
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${getCorrelationColor(analytics.currentValue)}`}>
                {analytics.currentValue.toFixed(2)}
              </div>
              <p className={`text-xs ${analytics.changePercent >= 0 ? 'text-orange-600' : 'text-green-600'}`}>
                {analytics.changePercent >= 0 ? '+' : ''}{analytics.changePercent.toFixed(3)} from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Status</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge className={getStatusColor(analytics.status)}>
                {analytics.status.charAt(0).toUpperCase() + analytics.status.slice(1)}
              </Badge>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold capitalize">{analytics.trend}</div>
              <p className="text-xs text-gray-600">Correlation direction</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Data Points</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.historicalData.length}</div>
              <p className="text-xs text-gray-600">Historical records</p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Historical Trend */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Historical Trend
              </CardTitle>
            </CardHeader>
            <CardContent>
              <AnalyticsChart
                data={filteredHistoricalData}
                dataKey="value"
                color="#f59e0b"
                unit=""
                height={300}
              />
            </CardContent>
          </Card>

          {/* Breakdown by Asset Class */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                Correlations by Asset Class
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.breakdown.byAssetClass.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{item.asset}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-orange-600 h-2 rounded-full"
                          style={{ width: `${Math.abs(item.value) * 100}%` }}
                        ></div>
                      </div>
                      <span className={`text-sm font-medium ${getCorrelationColor(item.value)}`}>
                        {item.value.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-4 w-full"
                onClick={() => handleDrillDown('Correlations by Asset Class', analytics.breakdown.byAssetClass, 'value', '#f59e0b', '')}
              >
                View Details
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Additional Breakdowns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* By Timeframe */}
          <Card>
            <CardHeader>
              <CardTitle>By Timeframe</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.breakdown.byTimeframe.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{item.timeframe}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${item.value * 100}%` }}
                        ></div>
                      </div>
                      <span className={`text-sm font-medium ${getCorrelationColor(item.value)}`}>
                        {item.value.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-4 w-full"
                onClick={() => handleDrillDown('Correlations by Timeframe', analytics.breakdown.byTimeframe, 'value', '#3b82f6', '')}
              >
                View Details
              </Button>
            </CardContent>
          </Card>

          {/* By Region */}
          <Card>
            <CardHeader>
              <CardTitle>By Region</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.breakdown.byRegion.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{item.region}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full"
                          style={{ width: `${item.value * 100}%` }}
                        ></div>
                      </div>
                      <span className={`text-sm font-medium ${getCorrelationColor(item.value)}`}>
                        {item.value.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-4 w-full"
                onClick={() => handleDrillDown('Correlations by Region', analytics.breakdown.byRegion, 'value', '#8b5cf6', '')}
              >
                View Details
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-orange-500" />
                Key Trends
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {analytics.insights.keyTrends.map((trend, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start">
                    <span className="text-orange-500 mr-2">•</span>
                    {trend}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                Risk Factors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {analytics.insights.riskFactors.map((risk, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start">
                    <span className="text-yellow-500 mr-2">•</span>
                    {risk}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-500" />
                Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {analytics.insights.recommendations.map((rec, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start">
                    <span className="text-blue-500 mr-2">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Filter Panel */}
      <FilterPanel
        isOpen={isFilterPanelOpen}
        onClose={() => setIsFilterPanelOpen(false)}
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        selectedMetrics={selectedMetrics}
        onMetricsChange={setSelectedMetrics}
        onApplyFilters={(filteredData) => setFilteredHistoricalData(filteredData)}
        historicalData={historicalData}
      />

      {/* Drill Down Modal */}
      <DrillDownModal
        isOpen={drillDownModal.isOpen}
        onClose={() => setDrillDownModal({ ...drillDownModal, isOpen: false })}
        title={drillDownModal.title}
        data={drillDownModal.data}
        dataKey={drillDownModal.dataKey}
        color={drillDownModal.color}
        unit={drillDownModal.unit}
        type={drillDownModal.type}
      />
    </DashboardLayout>
  )
}
