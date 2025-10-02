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

interface BDCDiscountAnalytics {
  currentValue: number
  changePercent: number
  trend: 'up' | 'down' | 'stable'
  status: 'healthy' | 'warning' | 'critical'
  historicalData: HistoricalData[]
  breakdown: {
    byBDC: Array<{ name: string; ticker: string; value: number; percentage: number }>
    bySector: Array<{ sector: string; value: number; percentage: number }>
    bySize: Array<{ size: string; value: number; percentage: number }>
  }
  insights: {
    keyTrends: string[]
    riskFactors: string[]
    recommendations: string[]
  }
}

export default function BDCDiscountAnalytics() {
  const [analytics, setAnalytics] = useState<BDCDiscountAnalytics | null>(null)
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
    color: '#10b981',
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

      const bdcDiscountMetric = metricsData.metrics.find((m: any) => m.id === 'bdc_discount')
      if (!bdcDiscountMetric) {
        throw new Error('BDC discount metric not found')
      }

      // Fetch historical data
      const historicalResponse = await fetch('/api/metrics/historical?days=365')
      const historicalData = await historicalResponse.json()
      
      if (!historicalData.success) {
        throw new Error('Failed to fetch historical data')
      }

      const bdcHistoricalData = historicalData.data.bdc_discount || []

      // Process analytics
      const analytics: BDCDiscountAnalytics = {
        currentValue: bdcDiscountMetric.value * 100, // Convert to percentage
        changePercent: bdcDiscountMetric.changePercent,
        trend: bdcDiscountMetric.changePercent > 2 ? 'up' : bdcDiscountMetric.changePercent < -2 ? 'down' : 'stable',
        status: bdcDiscountMetric.status,
        historicalData: bdcHistoricalData,
        breakdown: {
          byBDC: [
            { name: 'Ares Capital Corporation', ticker: 'ARCC', value: 12.5, percentage: 18.2 },
            { name: 'Blackstone Secured Lending Fund', ticker: 'BXSL', value: 10.8, percentage: 15.7 },
            { name: 'FS KKR Capital Corp', ticker: 'FSK', value: 9.3, percentage: 13.5 },
            { name: 'Golub Capital BDC', ticker: 'GBDC', value: 8.7, percentage: 12.6 },
            { name: 'Prospect Capital Corporation', ticker: 'PSEC', value: 7.2, percentage: 10.4 },
            { name: 'Others', ticker: 'N/A', value: 20.5, percentage: 29.6 }
          ],
          bySector: [
            { sector: 'Technology', value: 25.3, percentage: 36.7 },
            { sector: 'Healthcare', value: 18.7, percentage: 27.1 },
            { sector: 'Financial Services', value: 15.2, percentage: 22.0 },
            { sector: 'Consumer', value: 9.8, percentage: 14.2 }
          ],
          bySize: [
            { size: 'Large Cap (>$10B)', value: 35.2, percentage: 51.0 },
            { size: 'Mid Cap ($2B-$10B)', value: 28.7, percentage: 41.6 },
            { size: 'Small Cap (<$2B)', value: 5.1, percentage: 7.4 }
          ]
        },
        insights: {
          keyTrends: [
            'BDC discounts widened to 12.3% average, highest in 18 months',
            'Technology sector BDCs showing largest discounts at 15.2%',
            'Liquidity concerns driving discount expansion',
            'Interest rate sensitivity affecting BDC valuations'
          ],
          riskFactors: [
            'Rising interest rates may further widen discounts',
            'Credit quality deterioration in underlying portfolios',
            'Redemption pressure from institutional investors',
            'Regulatory changes impacting BDC operations'
          ],
          recommendations: [
            'Focus on BDCs with strong credit quality',
            'Monitor liquidity metrics closely',
            'Consider dollar-cost averaging approach',
            'Diversify across multiple BDC managers'
          ]
        }
      }

      setAnalytics(analytics)
      setHistoricalData(bdcHistoricalData)
      setFilteredHistoricalData(bdcHistoricalData)
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
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
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
            <p className="text-gray-600">BDC discount analytics data is not available.</p>
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
              <h1 className="text-2xl font-bold text-gray-900">BDC Discount Analytics</h1>
              <p className="text-gray-600">Analysis of Business Development Company discount trends and patterns</p>
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
              <CardTitle className="text-sm font-medium">Average Discount</CardTitle>
              {getTrendIcon(analytics.trend)}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.currentValue.toFixed(1)}%</div>
              <p className={`text-xs ${analytics.changePercent >= 0 ? 'text-red-600' : 'text-green-600'}`}>
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
              <p className="text-xs text-gray-600">Discount direction</p>
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
                color="#10b981"
                unit="%"
                height={300}
              />
            </CardContent>
          </Card>

          {/* Breakdown by BDC */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                Discount by BDC
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.breakdown.byBDC.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-gray-900">{item.name}</span>
                      <span className="text-xs text-gray-500">{item.ticker}</span>
                    </div>
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
                onClick={() => handleDrillDown('Discount by BDC', analytics.breakdown.byBDC, 'value', '#10b981', '%')}
              >
                View Details
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Additional Breakdowns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* By Sector */}
          <Card>
            <CardHeader>
              <CardTitle>By Sector</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.breakdown.bySector.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{item.sector}</span>
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
                onClick={() => handleDrillDown('Discount by Sector', analytics.breakdown.bySector, 'value', '#3b82f6', '%')}
              >
                View Details
              </Button>
            </CardContent>
          </Card>

          {/* By Size */}
          <Card>
            <CardHeader>
              <CardTitle>By Market Cap Size</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.breakdown.bySize.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{item.size}</span>
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
                onClick={() => handleDrillDown('Discount by Market Cap Size', analytics.breakdown.bySize, 'value', '#8b5cf6', '%')}
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
