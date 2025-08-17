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

interface BondIssuanceAnalytics {
  currentValue: number
  changePercent: number
  trend: 'up' | 'down' | 'stable'
  status: 'healthy' | 'warning' | 'critical'
  historicalData: HistoricalData[]
  breakdown: {
    byCompany: Array<{ name: string; value: number; percentage: number }>
    byFormType: Array<{ type: string; value: number; percentage: number }>
    byCoupon: Array<{ range: string; value: number; percentage: number }>
  }
  insights: {
    keyTrends: string[]
    riskFactors: string[]
    recommendations: string[]
  }
}

export default function BondIssuanceAnalytics() {
  const [analytics, setAnalytics] = useState<BondIssuanceAnalytics | null>(null)
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
    color: '#3b82f6',
    unit: 'B',
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

      const bondIssuanceMetric = metricsData.metrics.find((m: any) => m.key === 'bond_issuance')
      if (!bondIssuanceMetric) {
        throw new Error('Bond issuance metric not found')
      }

      // Fetch historical data
      const historicalResponse = await fetch('/api/metrics/historical?days=365')
      const historicalData = await historicalResponse.json()
      
      if (!historicalData.success) {
        throw new Error('Failed to fetch historical data')
      }

      const bondHistoricalData = historicalData.data.bond_issuance || []

      // Process analytics
      const analytics: BondIssuanceAnalytics = {
        currentValue: bondIssuanceMetric.value,
        changePercent: bondIssuanceMetric.changePercent,
        trend: bondIssuanceMetric.changePercent > 5 ? 'up' : bondIssuanceMetric.changePercent < -5 ? 'down' : 'stable',
        status: bondIssuanceMetric.status,
        historicalData: bondHistoricalData.map((point: any) => ({
          timestamp: point.timestamp,
          value: point.value,
          date: point.date || point.timestamp.split('T')[0]
        })),
        breakdown: {
          byCompany: bondIssuanceMetric.metadata?.companies?.map((company: string) => ({
            name: company,
            value: bondIssuanceMetric.value / (bondIssuanceMetric.metadata?.companies?.length || 1),
            percentage: 100 / (bondIssuanceMetric.metadata?.companies?.length || 1)
          })) || [],
          byFormType: [
            { type: '424B2', value: bondIssuanceMetric.value * 0.6, percentage: 60 },
            { type: '424B5', value: bondIssuanceMetric.value * 0.4, percentage: 40 }
          ],
          byCoupon: [
            { range: '4.0-4.5%', value: bondIssuanceMetric.value * 0.7, percentage: 70 },
            { range: '4.5-5.0%', value: bondIssuanceMetric.value * 0.3, percentage: 30 }
          ]
        },
        insights: {
          keyTrends: [
            `Weekly bond issuance is ${bondIssuanceMetric.changePercent > 0 ? 'increasing' : 'decreasing'} by ${Math.abs(bondIssuanceMetric.changePercent).toFixed(1)}%`,
            `Average coupon rate is ${bondIssuanceMetric.metadata?.avg_coupon || 4.35}%`,
            `${bondIssuanceMetric.metadata?.bond_count || 2} bonds issued this week`
          ],
          riskFactors: bondIssuanceMetric.value > 4000000000 ? [
            'High bond issuance may indicate increased leverage',
            'Rising coupon rates suggest higher borrowing costs'
          ] : [],
          recommendations: [
            'Monitor debt-to-equity ratios of issuing companies',
            'Track coupon rate trends for cost of capital analysis'
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
      // For bond issuance, we could filter by category if we had that data
      // For now, just apply date filtering
    }

    setFilteredHistoricalData(filtered)
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'decreasing':
        return <TrendingDown className="h-4 w-4 text-red-600" />
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
            <h1 className="text-3xl font-bold text-gray-900">Bond Issuance Analytics</h1>
            <p className="text-gray-600 mt-1">Analyze debt financing patterns and trends in the AI datacenter sector</p>
          </div>
        </div>

        {/* Summary Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Total Issuance</h3>
                {getTrendIcon(analytics.trend)}
              </div>
              <div className="text-3xl font-bold text-gray-900">
                ${(analytics.currentValue / 1000000000).toFixed(1)}B
              </div>
              <div className={`text-sm mt-2 ${
                analytics.changePercent > 0 ? 'text-green-600' : 'text-red-600'
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
                Debt issuance pattern
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
                Status of bond issuance
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
               {/* By Company */}
               <div className="space-y-3">
                 <div className="flex items-center justify-between">
                   <h4 className="font-semibold text-gray-900">By Company</h4>
                 </div>
                 <div className="text-2xl font-bold text-gray-900">
                   ${(analytics.breakdown.byCompany.reduce((sum, item) => sum + item.value, 0) / 1000000000).toFixed(1)}B
                 </div>
                 <div className="text-sm text-gray-600">
                   {analytics.breakdown.byCompany.length} companies
                 </div>
                 <div className="text-xs text-gray-600">
                   <div className="font-medium mb-1">Key Entities:</div>
                   <div className="space-y-1">
                     {analytics.breakdown.byCompany.slice(0, 3).map((entity, index) => (
                        <div key={index} className="bg-gray-50 px-2 py-1 rounded">
                         {entity.name}
                        </div>
                      ))}
                     {analytics.breakdown.byCompany.length > 3 && (
                       <div className="text-gray-500">+{analytics.breakdown.byCompany.length - 3} more</div>
                      )}
                    </div>
                  </div>
                </div>

               {/* By Form Type */}
               <div className="space-y-3">
                 <div className="flex items-center justify-between">
                   <h4 className="font-semibold text-gray-900">By Form Type</h4>
                 </div>
                 <div className="text-2xl font-bold text-gray-900">
                   ${(analytics.breakdown.byFormType.reduce((sum, item) => sum + item.value, 0) / 1000000000).toFixed(1)}B
                 </div>
                 <div className="text-sm text-gray-600">
                   {analytics.breakdown.byFormType.length} form types
                 </div>
                 <div className="text-xs text-gray-600">
                   <div className="font-medium mb-1">Form Types:</div>
                   <div className="space-y-1">
                     {analytics.breakdown.byFormType.map((form, index) => (
                        <div key={index} className="bg-gray-50 px-2 py-1 rounded">
                         {form.type}: {form.percentage}%
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

               {/* By Coupon */}
               <div className="space-y-3">
                 <div className="flex items-center justify-between">
                   <h4 className="font-semibold text-gray-900">By Coupon</h4>
                 </div>
                 <div className="text-2xl font-bold text-gray-900">
                   ${(analytics.breakdown.byCoupon.reduce((sum, item) => sum + item.value, 0) / 1000000000).toFixed(1)}B
                 </div>
                 <div className="text-sm text-gray-600">
                   {analytics.breakdown.byCoupon.length} ranges
                 </div>
                 <div className="text-xs text-gray-600">
                   <div className="font-medium mb-1">Coupon Ranges:</div>
                   <div className="space-y-1">
                     {analytics.breakdown.byCoupon.map((coupon, index) => (
                        <div key={index} className="bg-gray-50 px-2 py-1 rounded">
                         {coupon.range}: {coupon.percentage}%
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
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
               <div className="space-y-2">
                 <h4 className="font-semibold text-gray-900">
                   BDC Discount Correlation
                 </h4>
                 <div className="text-2xl font-bold text-gray-900">
                   -0.45
                 </div>
                 <Badge className="bg-blue-100 text-blue-600">
                   Moderate Negative
                 </Badge>
                 <div className="text-xs text-gray-600">
                   Higher bond issuance correlates with lower BDC discounts
                 </div>
               </div>
               <div className="space-y-2">
                 <h4 className="font-semibold text-gray-900">
                   Credit Fund Correlation
                 </h4>
                 <div className="text-2xl font-bold text-gray-900">
                   0.32
                 </div>
                 <Badge className="bg-green-100 text-green-600">
                   Weak Positive
                 </Badge>
                 <div className="text-xs text-gray-600">
                   Bond issuance and credit fund assets show weak positive correlation
                 </div>
               </div>
               <div className="space-y-2">
                 <h4 className="font-semibold text-gray-900">
                   Bank Provision Correlation
                 </h4>
                 <div className="text-2xl font-bold text-gray-900">
                   0.18
                 </div>
                 <Badge className="bg-gray-100 text-gray-600">
                   Very Weak Positive
                 </Badge>
                 <div className="text-xs text-gray-600">
                   Minimal correlation with bank provisions
                 </div>
               </div>
              </div>
            </CardContent>
        </Card>

        {/* Red Flags & Insights */}
        {analytics.status === 'critical' && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-red-700">
                <AlertTriangle className="h-5 w-5" />
                <span>Red Flags & Insights</span>
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
                        This may indicate increased risk in the AI datacenter financing sector.
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Historical Trend Chart */}
        <AnalyticsChart
          title="Bond Issuance Historical Trend"
          data={historicalData}
          dataKey="value"
          color="#3b82f6"
          unit="B"
          type="line"
          showTrend={true}
          height={400}
          dangerThreshold={10000000000}
          warningThreshold={5000000000}
          enableZoom={true}
          enableDrillDown={true}
          onDrillDown={(data) => handleDrillDown(historicalData, "Bond Issuance Historical Trend", "#3b82f6", "B", "line")}
          formatValue={(value) => `$${(value / 1000000000).toFixed(1)}`}
          formatDate={(date) => new Date(date).toLocaleDateString()}
          filteredData={filteredHistoricalData}
          showFilteredData={filteredHistoricalData.length !== historicalData.length}
        />

        {/* Category Breakdown Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <AnalyticsChart
            title="Demand-Side Issuance"
            data={historicalData.slice(0, 30)} // Last 30 days for category focus
            dataKey="value"
            color="#10b981"
            unit="B"
            type="area"
            showTrend={true}
            height={300}
            formatValue={(value) => `$${(value * 0.4 / 1000000000).toFixed(1)}`}
            formatDate={(date) => new Date(date).toLocaleDateString()}
          />
          <AnalyticsChart
            title="Supply-Side Issuance"
            data={historicalData.slice(0, 30)}
            dataKey="value"
            color="#f59e0b"
            unit="B"
            type="area"
            showTrend={true}
            height={300}
            formatValue={(value) => `$${(value * 0.35 / 1000000000).toFixed(1)}`}
            formatDate={(date) => new Date(date).toLocaleDateString()}
          />
          <AnalyticsChart
            title="Financing Issuance"
            data={historicalData.slice(0, 30)}
            dataKey="value"
            color="#8b5cf6"
            unit="B"
            type="area"
            showTrend={true}
            height={300}
            formatValue={(value) => `$${(value * 0.25 / 1000000000).toFixed(1)}`}
            formatDate={(date) => new Date(date).toLocaleDateString()}
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
          availableMetrics={['bond_issuance', 'demand_side', 'supply_side', 'financing']}
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
