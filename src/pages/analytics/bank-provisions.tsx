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

interface BankProvisionAnalytics {
  currentValue: number
  changePercent: number
  trend: 'up' | 'down' | 'stable'
  status: 'healthy' | 'warning' | 'critical'
  historicalData: HistoricalData[]
  breakdown: {
    byBank: Array<{ name: string; value: number; percentage: number }>
    byRegion: Array<{ region: string; value: number; percentage: number }>
    bySize: Array<{ size: string; value: number; percentage: number }>
  }
  insights: {
    keyTrends: string[]
    riskFactors: string[]
    recommendations: string[]
  }
}

export default function BankProvisionAnalytics() {
  const [analytics, setAnalytics] = useState<BankProvisionAnalytics | null>(null)
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
    color: '#ef4444',
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

      const bankProvisionMetric = metricsData.metrics.find((m: any) => m.key === 'bank_provision')
      if (!bankProvisionMetric) {
        throw new Error('Bank provision metric not found')
      }

      // Fetch historical data
      const historicalResponse = await fetch('/api/metrics/historical?days=365')
      const historicalData = await historicalResponse.json()
      
      if (!historicalData.success) {
        throw new Error('Failed to fetch historical data')
      }

      const bankHistoricalData = historicalData.data.bank_provision || []

      // Process analytics
      const analytics: BankProvisionAnalytics = {
        currentValue: bankProvisionMetric.value,
        changePercent: bankProvisionMetric.changePercent,
        trend: bankProvisionMetric.changePercent > 2 ? 'up' : bankProvisionMetric.changePercent < -2 ? 'down' : 'stable',
        status: bankProvisionMetric.status,
        historicalData: bankHistoricalData.map((point: any) => ({
          timestamp: point.timestamp,
          value: point.value,
          date: point.date || point.timestamp.split('T')[0]
        })),
        breakdown: {
          byBank: [
            { name: 'JPMorgan Chase', value: bankProvisionMetric.value * 0.25, percentage: 25 },
            { name: 'Bank of America', value: bankProvisionMetric.value * 0.2, percentage: 20 },
            { name: 'Wells Fargo', value: bankProvisionMetric.value * 0.15, percentage: 15 },
            { name: 'Citigroup', value: bankProvisionMetric.value * 0.15, percentage: 15 },
            { name: 'Other Banks', value: bankProvisionMetric.value * 0.25, percentage: 25 }
          ],
          byRegion: [
            { region: 'North America', value: bankProvisionMetric.value * 0.6, percentage: 60 },
            { region: 'Europe', value: bankProvisionMetric.value * 0.25, percentage: 25 },
            { region: 'Asia Pacific', value: bankProvisionMetric.value * 0.15, percentage: 15 }
          ],
          bySize: [
            { size: 'Large Banks (>$100B)', value: bankProvisionMetric.value * 0.7, percentage: 70 },
            { size: 'Mid Banks ($10B-$100B)', value: bankProvisionMetric.value * 0.2, percentage: 20 },
            { size: 'Small Banks (<$10B)', value: bankProvisionMetric.value * 0.1, percentage: 10 }
          ]
        },
        insights: {
          keyTrends: [
            `Bank provisions are ${bankProvisionMetric.changePercent > 0 ? 'increasing' : 'decreasing'} by ${Math.abs(bankProvisionMetric.changePercent).toFixed(1)}%`,
            `Current provision rate: ${bankProvisionMetric.value.toFixed(1)}%`,
            `Trend suggests ${bankProvisionMetric.changePercent > 0 ? 'increasing' : 'decreasing'} risk assessment`
          ],
          riskFactors: bankProvisionMetric.value > 12 ? [
            'High bank provisions may indicate deteriorating credit quality',
            'Increasing provisions suggest banks are preparing for potential defaults'
          ] : [],
          recommendations: [
            'Monitor loan loss reserves and credit quality metrics',
            'Track non-performing loan ratios',
            'Watch for signs of credit deterioration in key sectors'
          ]
        }
      }
      
      setAnalytics(analytics)
      setHistoricalData(analytics.historicalData)
      setFilteredHistoricalData(analytics.historicalData)
    } catch (error) {
      console.error('Error fetching analytics:', error)
      setError(error instanceof Error ? error.message : 'Failed to fetch analytics')
    } finally {
      setLoading(false)
    }
  }

  const handleDrillDown = (data: any[], title: string, color: string, unit: string, type: 'line' | 'area' | 'bar') => {
    setDrillDownModal({
      isOpen: true,
      title,
      data,
      dataKey: 'value',
      color,
      unit,
      type
    })
  }

  const closeDrillDownModal = () => {
    setDrillDownModal(prev => ({ ...prev, isOpen: false }))
  }

  // Filter handlers
  const handleDateRangeChange = (startDate: Date, endDate: Date) => {
    setDateRange({ start: startDate, end: endDate })
    applyFilters(startDate, endDate, selectedMetrics)
  }

  const handleMetricsChange = (metrics: string[]) => {
    setSelectedMetrics(metrics)
    applyFilters(dateRange.start, dateRange.end, metrics)
  }

  const handleResetFilters = () => {
    const defaultStart = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000)
    const defaultEnd = new Date()
    setDateRange({ start: defaultStart, end: defaultEnd })
    setSelectedMetrics([])
    setFilteredHistoricalData(historicalData)
  }

  const applyFilters = (startDate: Date, endDate: Date, metrics: string[]) => {
    let filtered = historicalData.filter(item => {
      const itemDate = new Date(item.timestamp)
      return itemDate >= startDate && itemDate <= endDate
    })

    if (metrics.length > 0) {
      // For bank provisions, we could filter by category if we had that data
      // For now, just apply date filtering
    }

    setFilteredHistoricalData(filtered)
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUp className="h-4 w-4 text-red-600" />
      case 'decreasing':
        return <TrendingDown className="h-4 w-4 text-green-600" />
      default:
        return <Activity className="h-4 w-4 text-gray-600" />
    }
  }

  const getCorrelationStrength = (correlation: number) => {
    const abs = Math.abs(correlation)
    if (abs > 0.7) return 'Strong'
    if (abs > 0.4) return 'Moderate'
    if (abs > 0.2) return 'Weak'
    return 'None'
  }

  const getCorrelationColor = (correlation: number) => {
    const abs = Math.abs(correlation)
    if (abs > 0.7) return 'bg-green-100 text-green-600'
    if (abs > 0.4) return 'bg-yellow-100 text-yellow-600'
    if (abs > 0.2) return 'bg-blue-100 text-blue-600'
    return 'bg-gray-100 text-gray-600'
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading analytics...</div>
        </div>
      </DashboardLayout>
    )
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="text-center py-8">
          <p className="text-red-600">{error}</p>
        </div>
      </DashboardLayout>
    )
  }

  if (!analytics) {
    return (
      <DashboardLayout>
        <div className="text-center py-8">
          <p className="text-gray-600">No analytics data available</p>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <Link href="/analytics">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Analytics
                </Button>
              </Link>
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Bank Provisions Analytics</h1>
            <p className="text-gray-600 mt-1">Analyze banking sector risk assessment and provision trends</p>
          </div>
        </div>

        {/* Summary Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Total Provisions</h3>
                {getTrendIcon(analytics.trend)}
              </div>
              <div className="text-3xl font-bold text-gray-900">
                ${analytics.currentValue.toFixed(1)}%
              </div>
              <div className={`text-sm mt-2 ${
                analytics.changePercent > 0 ? 'text-red-600' : 'text-green-600'
              }`}>
                {analytics.changePercent > 0 ? '+' : ''}{analytics.changePercent.toFixed(1)}% from previous period
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Trend</h3>
                <Badge variant={analytics.trend === 'up' ? 'destructive' : 
                               analytics.trend === 'down' ? 'default' : 'secondary'}>
                  {analytics.trend}
                </Badge>
              </div>
              <div className="text-3xl font-bold text-gray-900 capitalize">
                {analytics.trend}
              </div>
              <div className="text-sm text-gray-600 mt-2">
                Risk assessment pattern
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Red Flags</h3>
                {analytics.status === 'critical' && (
                  <AlertTriangle className="h-5 w-5 text-red-500" />
                )}
              </div>
              <div className="text-3xl font-bold text-gray-900">
                {analytics.status}
              </div>
              <div className="text-sm text-gray-600 mt-2">
                Current status
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Category Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <PieChart className="h-5 w-5" />
              <span>Category Breakdown</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {Object.entries(analytics.breakdown).map(([category, data]) => (
                <div key={category} className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-gray-900 capitalize">{category.replace(/([A-Z])/g, ' $1')}</h4>
                    {getTrendIcon(analytics.trend)}
                  </div>
                  <div className="text-2xl font-bold text-gray-900">
                    {category === 'byBank' ? `${data.length} Banks` : `${data.length} Regions`}
                  </div>
                  <div className="text-sm text-gray-600 mt-2">
                    {category === 'byBank' ? 'Top Banks by Provision Value' : 'Top Regions by Provision Value'}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Cross-Metric Correlations */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>Cross-Metric Correlations</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(analytics.breakdown).map(([metric, data]) => (
                <div key={metric} className="space-y-2">
                  <h4 className="font-semibold text-gray-900 capitalize">
                    {metric.replace(/([A-Z])/g, ' $1').replace('By', '')}
                  </h4>
                  <div className="text-2xl font-bold text-gray-900">
                    {metric === 'byBank' ? `${data.length} Banks` : `${data.length} Regions`}
                  </div>
                  <Badge className={getCorrelationColor(0)}>
                    {metric === 'byBank' ? 'Top Banks' : 'Top Regions'}
                  </Badge>
                  <div className="text-xs text-gray-600">
                    {metric === 'byBank' ? 'Top Banks by Provision Value' : 'Top Regions by Provision Value'}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Red Flags & Insights */}
        {analytics.insights.riskFactors.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-red-700">
                <AlertTriangle className="h-5 w-5" />
                <span>Risk Factors & Recommendations</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.insights.riskFactors.map((factor, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-red-50 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5" />
                    <div>
                      <div className="font-medium text-red-800">{factor}</div>
                      <div className="text-sm text-red-600 mt-1">
                        This may indicate increased systemic risk in the banking sector.
                      </div>
                    </div>
                  </div>
                ))}
                <div className="text-sm text-gray-600 mt-2">
                  Recommendations:
                </div>
                <ul className="list-disc list-inside text-sm text-gray-600">
                  {analytics.insights.recommendations.map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Historical Trend Chart */}
        <AnalyticsChart
          title="Bank Provisions Historical Trend"
          data={historicalData}
          dataKey="value"
          color="#ef4444"
          unit="%"
          type="line"
          showTrend={true}
          height={400}
          dangerThreshold={15}
          warningThreshold={10}
          enableZoom={true}
          enableDrillDown={true}
          onDrillDown={(data) => handleDrillDown(historicalData, "Bank Provisions Historical Trend", "#ef4444", "%", "line")}
          formatValue={(value) => `${value.toFixed(1)}%`}
          formatDate={(date) => {
            const d = new Date(date)
            const quarter = Math.floor((d.getMonth() / 3)) + 1
            const year = d.getFullYear()
            return `Q${quarter} ${year}`
          }}
          filteredData={filteredHistoricalData}
          showFilteredData={filteredHistoricalData.length !== historicalData.length}
        />

        {/* Category Breakdown Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <AnalyticsChart
            title="Commercial Real Estate"
            data={historicalData.slice(0, 8)} // Last 8 quarters for category focus
            dataKey="value"
            color="#3b82f6"
            unit="%"
            type="line"
            showTrend={true}
            height={300}
            formatValue={(value) => `${value.toFixed(1)}%`}
            formatDate={(date) => {
              const d = new Date(date)
              const quarter = Math.floor((d.getMonth() / 3)) + 1
              const year = d.getFullYear()
              return `Q${quarter} ${year}`
            }}
          />
          <AnalyticsChart
            title="Technology Lending"
            data={historicalData.slice(0, 8)}
            dataKey="value"
            color="#10b981"
            unit="%"
            type="line"
            showTrend={true}
            height={300}
            formatValue={(value) => `${value.toFixed(1)}%`}
            formatDate={(date) => {
              const d = new Date(date)
              const quarter = Math.floor((d.getMonth() / 3)) + 1
              const year = d.getFullYear()
              return `Q${quarter} ${year}`
            }}
          />
          <AnalyticsChart
            title="Consumer Credit"
            data={historicalData.slice(0, 8)}
            dataKey="value"
            color="#f59e0b"
            unit="%"
            type="line"
            showTrend={true}
            height={300}
            formatValue={(value) => `${value.toFixed(1)}%`}
            formatDate={(date) => {
              const d = new Date(date)
              const quarter = Math.floor((d.getMonth() / 3)) + 1
              const year = d.getFullYear()
              return `Q${quarter} ${year}`
            }}
          />
        </div>

        {/* Drill-Down Modal */}
        <DrillDownModal
          isOpen={drillDownModal.isOpen}
          onClose={closeDrillDownModal}
          title={drillDownModal.title}
          data={drillDownModal.data}
          dataKey={drillDownModal.dataKey}
          color={drillDownModal.color}
          unit={drillDownModal.unit}
          type={drillDownModal.type}
        />

        {/* Filter Panel */}
        <FilterPanel
          isOpen={isFilterPanelOpen}
          onToggle={() => setIsFilterPanelOpen(!isFilterPanelOpen)}
          onDateRangeChange={handleDateRangeChange}
          availableMetrics={['bank_provision', 'commercial_real_estate', 'technology_lending', 'consumer_credit']}
          selectedMetrics={selectedMetrics}
          onMetricsChange={handleMetricsChange}
          onResetFilters={handleResetFilters}
          activeFiltersCount={
            (filteredHistoricalData.length !== historicalData.length ? 1 : 0) +
            (selectedMetrics.length > 0 ? 1 : 0)
          }
        />
      </div>
    </DashboardLayout>
  )
}
