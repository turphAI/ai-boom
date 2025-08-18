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

interface CreditFundAnalytics {
  currentValue: number
  changePercent: number
  trend: 'up' | 'down' | 'stable'
  status: 'healthy' | 'warning' | 'critical'
  historicalData: HistoricalData[]
  breakdown: {
    byFund: Array<{ name: string; ticker: string; value: number; percentage: number }>
    byStrategy: Array<{ strategy: string; value: number; percentage: number }>
    byDuration: Array<{ duration: string; value: number; percentage: number }>
  }
  insights: {
    keyTrends: string[]
    riskFactors: string[]
    recommendations: string[]
  }
}

export default function CreditFundAnalytics() {
  const [analytics, setAnalytics] = useState<CreditFundAnalytics | null>(null)
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
    color: '#8b5cf6',
    unit: '%',
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

      const creditFundMetric = metricsData.metrics.find((m: any) => m.id === 'credit-fund')
      if (!creditFundMetric) {
        throw new Error('Credit fund metric not found')
      }

      // Fetch historical data
      const historicalResponse = await fetch('/api/metrics/historical?days=365')
      const historicalData = await historicalResponse.json()
      
      if (!historicalData.success) {
        throw new Error('Failed to fetch historical data')
      }

      const creditHistoricalData = historicalData.data.credit_fund || []

      // Process analytics
      const analytics: CreditFundAnalytics = {
        currentValue: creditFundMetric.value,
        changePercent: creditFundMetric.changePercent,
        trend: creditFundMetric.changePercent > 1 ? 'up' : creditFundMetric.changePercent < -1 ? 'down' : 'stable',
        status: creditFundMetric.status,
        historicalData: creditHistoricalData,
        breakdown: {
          byFund: [
            { name: 'PIMCO Income Fund', ticker: 'PIMIX', value: 4.2, percentage: 18.3 },
            { name: 'DoubleLine Total Return', ticker: 'DLTNX', value: 3.8, percentage: 16.5 },
            { name: 'Metropolitan West Total Return', ticker: 'MWTRX', value: 3.5, percentage: 15.2 },
            { name: 'Dodge & Cox Income Fund', ticker: 'DODIX', value: 3.2, percentage: 13.9 },
            { name: 'Vanguard Total Bond Market', ticker: 'VBTLX', value: 2.9, percentage: 12.6 },
            { name: 'Others', ticker: 'N/A', value: 5.4, percentage: 23.5 }
          ],
          byStrategy: [
            { strategy: 'Core Bond', value: 8.5, percentage: 37.0 },
            { strategy: 'High Yield', value: 6.2, percentage: 27.0 },
            { strategy: 'Municipal', value: 4.8, percentage: 20.9 },
            { strategy: 'Emerging Markets', value: 3.5, percentage: 15.1 }
          ],
          byDuration: [
            { duration: 'Short Term (<3 years)', value: 5.2, percentage: 22.6 },
            { duration: 'Intermediate (3-10 years)', value: 12.8, percentage: 55.7 },
            { duration: 'Long Term (>10 years)', value: 5.0, percentage: 21.7 }
          ]
        },
        insights: {
          keyTrends: [
            'Credit fund yields increased 25 basis points over the quarter',
            'High yield strategies showing strongest performance',
            'Duration positioning driving relative returns',
            'Credit quality spreads tightening across sectors'
          ],
          riskFactors: [
            'Interest rate volatility affecting duration strategies',
            'Credit spread widening in high yield sector',
            'Liquidity concerns in emerging market debt',
            'Regulatory changes impacting fund flows'
          ],
          recommendations: [
            'Maintain diversified duration exposure',
            'Monitor credit quality trends closely',
            'Consider tactical allocation to high yield',
            'Review liquidity management strategies'
          ]
        }
      }

      setAnalytics(analytics)
      setHistoricalData(creditHistoricalData)
      setFilteredHistoricalData(creditHistoricalData)
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
      case 'up': return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'down': return <TrendingDown className="h-4 w-4 text-red-500" />
      default: return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
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
            <p className="text-gray-600">Credit fund analytics data is not available.</p>
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
              <h1 className="text-2xl font-bold text-gray-900">Credit Fund Analytics</h1>
              <p className="text-gray-600">Analysis of credit fund performance and yield trends</p>
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
              <CardTitle className="text-sm font-medium">Average Yield</CardTitle>
              {getTrendIcon(analytics.trend)}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.currentValue.toFixed(2)}%</div>
              <p className={`text-xs ${analytics.changePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {analytics.changePercent >= 0 ? '+' : ''}{analytics.changePercent.toFixed(1)}% from last month
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
              <p className="text-xs text-gray-600">Yield direction</p>
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
                color="#8b5cf6"
                unit="%"
                height={300}
              />
            </CardContent>
          </Card>

          {/* Breakdown by Fund */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                Yields by Fund
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.breakdown.byFund.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-gray-900">{item.name}</span>
                      <span className="text-xs text-gray-500">{item.ticker}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full"
                          style={{ width: `${item.percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">{item.value.toFixed(1)}%</span>
                    </div>
                  </div>
                ))}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-4 w-full"
                onClick={() => handleDrillDown('Yields by Fund', analytics.breakdown.byFund, 'value', '#8b5cf6', '%')}
              >
                View Details
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Additional Breakdowns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* By Strategy */}
          <Card>
            <CardHeader>
              <CardTitle>By Strategy</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.breakdown.byStrategy.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{item.strategy}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${item.percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">{item.value.toFixed(1)}%</span>
                    </div>
                  </div>
                ))}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-4 w-full"
                onClick={() => handleDrillDown('Yields by Strategy', analytics.breakdown.byStrategy, 'value', '#3b82f6', '%')}
              >
                View Details
              </Button>
            </CardContent>
          </Card>

          {/* By Duration */}
          <Card>
            <CardHeader>
              <CardTitle>By Duration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.breakdown.byDuration.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{item.duration}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{ width: `${item.percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">{item.value.toFixed(1)}%</span>
                    </div>
                  </div>
                ))}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-4 w-full"
                onClick={() => handleDrillDown('Yields by Duration', analytics.breakdown.byDuration, 'value', '#10b981', '%')}
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
                <TrendingUp className="h-5 w-5 text-green-500" />
                Key Trends
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {analytics.insights.keyTrends.map((trend, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start">
                    <span className="text-green-500 mr-2">•</span>
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
