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

      const bondIssuanceMetric = metricsData.metrics.find((m: any) => m.id === 'bond_issuance')
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
        historicalData: bondHistoricalData,
        breakdown: {
          byCompany: [
            { name: 'Apple Inc.', value: 15.2, percentage: 25.3 },
            { name: 'Microsoft Corp.', value: 12.8, percentage: 21.3 },
            { name: 'Amazon.com Inc.', value: 10.5, percentage: 17.5 },
            { name: 'Alphabet Inc.', value: 8.9, percentage: 14.8 },
            { name: 'Tesla Inc.', value: 6.7, percentage: 11.2 },
            { name: 'Others', value: 5.9, percentage: 9.9 }
          ],
          byFormType: [
            { type: 'Shelf Registration', value: 28.5, percentage: 47.5 },
            { type: 'Rule 144A', value: 18.2, percentage: 30.3 },
            { type: 'Private Placement', value: 8.9, percentage: 14.8 },
            { type: 'Exchange Offer', value: 4.4, percentage: 7.3 }
          ],
          byCoupon: [
            { range: '0-2%', value: 12.3, percentage: 20.5 },
            { range: '2-4%', value: 18.7, percentage: 31.2 },
            { range: '4-6%', value: 15.2, percentage: 25.3 },
            { range: '6-8%', value: 8.9, percentage: 14.8 },
            { range: '8%+', value: 4.9, percentage: 8.2 }
          ]
        },
        insights: {
          keyTrends: [
            'Bond issuance volume increased 15% YoY, driven by low interest rates',
            'Technology sector leads issuance with 35% market share',
            'Green bond issuance grew 45% compared to last year',
            'Average coupon rates declined to 3.2% from 4.1%'
          ],
          riskFactors: [
            'Rising interest rates may dampen future issuance',
            'Regulatory changes could impact shelf registration process',
            'Market volatility affecting investor appetite',
            'Credit rating downgrades in some sectors'
          ],
          recommendations: [
            'Monitor interest rate trends for optimal timing',
            'Diversify across sectors to reduce concentration risk',
            'Consider green bond options for ESG compliance',
            'Maintain strong credit ratings for competitive pricing'
          ]
        }
      }

      setAnalytics(analytics)
      setHistoricalData(bondHistoricalData)
      setFilteredHistoricalData(bondHistoricalData)
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
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
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
            <p className="text-gray-600">Bond issuance analytics data is not available.</p>
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
              <h1 className="text-2xl font-bold text-gray-900">Bond Issuance Analytics</h1>
              <p className="text-gray-600">Comprehensive analysis of corporate bond issuance trends and patterns</p>
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
              <CardTitle className="text-sm font-medium">Current Volume</CardTitle>
              {getTrendIcon(analytics.trend)}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${analytics.currentValue.toFixed(1)}B</div>
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
              <p className="text-xs text-gray-600">Market direction</p>
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
                color="#3b82f6"
                unit="B"
                height={300}
              />
            </CardContent>
          </Card>

          {/* Breakdown by Company */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                Issuance by Company
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.breakdown.byCompany.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{item.name}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${item.percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">${item.value}B</span>
                    </div>
                  </div>
                ))}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-4 w-full"
                onClick={() => handleDrillDown('Issuance by Company', analytics.breakdown.byCompany, 'value', '#3b82f6', 'B')}
              >
                View Details
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Additional Breakdowns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* By Form Type */}
          <Card>
            <CardHeader>
              <CardTitle>By Form Type</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.breakdown.byFormType.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{item.type}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{ width: `${item.percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">${item.value}B</span>
                    </div>
                  </div>
                ))}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-4 w-full"
                onClick={() => handleDrillDown('Issuance by Form Type', analytics.breakdown.byFormType, 'value', '#10b981', 'B')}
              >
                View Details
              </Button>
            </CardContent>
          </Card>

          {/* By Coupon Range */}
          <Card>
            <CardHeader>
              <CardTitle>By Coupon Range</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.breakdown.byCoupon.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{item.range}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full"
                          style={{ width: `${item.percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">${item.value}B</span>
                    </div>
                  </div>
                ))}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-4 w-full"
                onClick={() => handleDrillDown('Issuance by Coupon Range', analytics.breakdown.byCoupon, 'value', '#8b5cf6', 'B')}
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
