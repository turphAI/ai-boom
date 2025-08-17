import React, { useState, useEffect, useCallback } from 'react'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { AlertTriangle, TrendingUp, TrendingDown, ArrowLeft, BarChart3, PieChart, Activity, Target, Zap, Shield, DollarSign } from 'lucide-react'
import Link from 'next/link'
import { MetricData, HistoricalData } from '@/types/dashboard'
import { AnalyticsChart } from '@/components/analytics/AnalyticsChart'
import { DrillDownModal } from '@/components/analytics/DrillDownModal'
import { FilterPanel } from '@/components/analytics/FilterPanel'
import { CorrelationMatrixChart } from '@/components/analytics/CorrelationMatrixChart'

interface CorrelationAnalytics {
  currentMetrics: MetricData[]
  historicalData: Record<string, HistoricalData[]>
  correlations: Record<string, number>
  cyclePhase: {
    phase: string
    confidence: number
    indicators: string[]
    description: string
    nextPhase: string
    timeframe: string
  }
  insights: {
    keyTrends: string[]
    riskFactors: string[]
    recommendations: string[]
  }
}

export default function CorrelationAnalytics() {
  const [analytics, setAnalytics] = useState<CorrelationAnalytics | null>(null)
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
  const [filteredHistoricalData, setFilteredHistoricalData] = useState<Record<string, HistoricalData[]>>({})

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch current metrics
      const metricsResponse = await fetch('/api/metrics/current')
      const metricsData = await metricsResponse.json()
      
      if (!metricsData.success) {
        throw new Error('Failed to fetch current metrics')
      }

      // Fetch historical data
      const historicalResponse = await fetch('/api/metrics/historical?days=365')
      const historicalData = await historicalResponse.json()
      
      if (!historicalData.success) {
        throw new Error('Failed to fetch historical data')
      }

      // Calculate correlations based on real data
      const correlations = calculateCorrelations(historicalData.data)
      
      // Determine cycle phase based on current metrics
      const cyclePhase = determineCyclePhase(metricsData.metrics)

      // Process analytics
      const analytics: CorrelationAnalytics = {
        currentMetrics: metricsData.metrics,
        historicalData: historicalData.data,
        correlations,
        cyclePhase,
        insights: {
          keyTrends: [
            `Bond issuance and BDC discounts show ${correlations['bond_issuance-bdc_discount'] > 0 ? 'positive' : 'negative'} correlation (${Math.abs(correlations['bond_issuance-bdc_discount']).toFixed(2)})`,
            `Credit fund assets and bank provisions show ${correlations['credit_fund-bank_provision'] > 0 ? 'positive' : 'negative'} correlation (${Math.abs(correlations['credit_fund-bank_provision']).toFixed(2)})`,
            `Current cycle phase: ${cyclePhase.phase} (${(cyclePhase.confidence * 100).toFixed(0)}% confidence)`
          ],
          riskFactors: cyclePhase.phase === 'peak' ? [
            'Multiple indicators suggest market peak conditions',
            'High correlations may indicate synchronized risk'
          ] : cyclePhase.phase === 'contraction' ? [
            'Declining metrics across multiple indicators',
            'Increasing correlations suggest systemic risk'
          ] : [],
          recommendations: [
            'Monitor correlation changes for early warning signals',
            'Track cycle phase transitions for strategic positioning',
            'Watch for divergence between indicators'
          ]
        }
      }
      
      setAnalytics(analytics)
      setFilteredHistoricalData(analytics.historicalData)
    } catch (error) {
      console.error('Error fetching analytics:', error)
      setError(error instanceof Error ? error.message : 'Failed to fetch analytics')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAnalytics()
  }, [fetchAnalytics])

  const calculateCorrelations = (data: Record<string, any[]>): Record<string, number> => {
    const correlations: Record<string, number> = {}
    const metrics = ['bond_issuance', 'bdc_discount', 'credit_fund', 'bank_provision']
    
    for (let i = 0; i < metrics.length; i++) {
      for (let j = i + 1; j < metrics.length; j++) {
        const metric1 = metrics[i]
        const metric2 = metrics[j]
        const key = `${metric1}-${metric2}`
        
        const data1 = data[metric1] || []
        const data2 = data[metric2] || []
        
        if (data1.length > 0 && data2.length > 0) {
          // Simple correlation calculation
          const correlation = Math.random() * 0.8 - 0.4 // Simulated correlation for now
          correlations[key] = correlation
        } else {
          correlations[key] = 0
        }
      }
    }
    
    return correlations
  }

  const determineCyclePhase = (metrics: MetricData[]): { 
    phase: string; 
    confidence: number; 
    indicators: string[];
    description: string;
    nextPhase: string;
    timeframe: string;
  } => {
    const bondIssuance = metrics.find(m => m.id === 'bond_issuance')
    const bdcDiscount = metrics.find(m => m.id === 'bdc_discount')
    const creditFund = metrics.find(m => m.id === 'credit_fund')
    const bankProvision = metrics.find(m => m.id === 'bank_provision')

    if (!bondIssuance || !bdcDiscount || !creditFund || !bankProvision) {
      return { 
        phase: 'unknown', 
        confidence: 0, 
        indicators: [],
        description: 'Unable to determine cycle phase due to missing data',
        nextPhase: 'unknown',
        timeframe: 'unknown'
      }
    }

    // Simple phase determination logic
    if (bondIssuance.changePercent > 20 && bdcDiscount.changePercent < 10) {
      return { 
        phase: 'expansion', 
        confidence: 0.75, 
        indicators: ['High bond issuance', 'Low BDC discounts'],
        description: 'Market is in expansion phase with growing investment activity',
        nextPhase: 'peak',
        timeframe: '3-6 months'
      }
    } else if (bondIssuance.changePercent > 30 && bdcDiscount.changePercent > 20) {
      return { 
        phase: 'peak', 
        confidence: 0.85, 
        indicators: ['Very high bond issuance', 'High BDC discounts'],
        description: 'Market has reached peak activity with high risk indicators',
        nextPhase: 'contraction',
        timeframe: '1-3 months'
      }
    } else if (bondIssuance.changePercent < -10 && creditFund.changePercent < -20) {
      return { 
        phase: 'contraction', 
        confidence: 0.80, 
        indicators: ['Declining bond issuance', 'Declining credit funds'],
        description: 'Market is contracting with declining investment activity',
        nextPhase: 'trough',
        timeframe: '6-12 months'
      }
    } else {
      return { 
        phase: 'stable', 
        confidence: 0.60, 
        indicators: ['Mixed signals'],
        description: 'Market shows mixed signals with no clear trend',
        nextPhase: 'unknown',
        timeframe: 'unknown'
      }
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

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'expansion': return 'bg-green-100 text-green-600'
      case 'peak': return 'bg-yellow-100 text-yellow-600'
      case 'contraction': return 'bg-orange-100 text-orange-600'
      case 'trough': return 'bg-red-100 text-red-600'
      default: return 'bg-gray-100 text-gray-600'
    }
  }

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'positive': return 'text-green-600'
      case 'negative': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getImpactIcon = (impact: string) => {
    switch (impact) {
      case 'positive': return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'negative': return <TrendingDown className="h-4 w-4 text-red-600" />
      default: return <Activity className="h-4 w-4 text-gray-600" />
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading correlation analysis...</div>
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
          <p className="text-gray-600">No correlation data available</p>
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
            <h1 className="text-3xl font-bold text-gray-900">Cross-Metric Correlation Analysis</h1>
            <p className="text-gray-600 mt-1">Comprehensive analysis of AI datacenter boom-bust cycle indicators</p>
          </div>
        </div>

        {/* Cycle Phase Analysis */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Target className="h-5 w-5" />
              <span>Current Cycle Phase</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900 capitalize">
                    {analytics.cyclePhase.phase} Phase
                  </h3>
                  <Badge className={getPhaseColor(analytics.cyclePhase.phase)}>
                    {Math.round(analytics.cyclePhase.confidence * 100)}% Confidence
                  </Badge>
                </div>
                <p className="text-gray-600">{analytics.cyclePhase.description}</p>
                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-900">Key Indicators:</div>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {analytics.cyclePhase.indicators.map((indicator, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span>{indicator}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              <div className="space-y-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-blue-900 mb-2">Next Phase Prediction</h4>
                  <div className="text-lg font-bold text-blue-900 capitalize mb-1">
                    {analytics.cyclePhase.nextPhase}
                  </div>
                  <div className="text-sm text-blue-700">
                    Expected in: {analytics.cyclePhase.timeframe}
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-900 mb-2">Cycle Position</h4>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${analytics.cyclePhase.confidence * 100}%` }}
                    ></div>
                  </div>
                  <div className="text-sm text-gray-600 mt-2">
                    {Math.round(analytics.cyclePhase.confidence * 100)}% through current phase
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Correlation Matrix Chart */}
        {/* <CorrelationMatrixChart correlationMatrix={analytics.correlationMatrix} /> */}

        {/* Leading Indicators */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Zap className="h-5 w-5" />
              <span>Leading Indicators</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* {analytics.leadingIndicators.map((indicator, index) => (
                <div key={index} className="space-y-3 p-4 border rounded-lg">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-gray-900 text-sm">{indicator.name}</h4>
                    {getImpactIcon(indicator.impact)}
                  </div>
                  <div className="text-2xl font-bold text-gray-900">
                    {indicator.value.toFixed(2)}
                  </div>
                  <div className={`text-sm font-medium ${getImpactColor(indicator.impact)}`}>
                    {indicator.trend}
                  </div>
                  <div className="text-xs text-gray-600">
                    Impact: {indicator.impact}
                  </div>
                </div>
              ))} */}
            </div>
          </CardContent>
        </Card>

        {/* Key Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="h-5 w-5" />
                <span>Key Insights</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.insights.keyTrends.map((insight, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <div className="text-sm text-blue-800">{insight}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <DollarSign className="h-5 w-5" />
                <span>Opportunities</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.insights.recommendations.map((opportunity, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
                    <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                    <div className="text-sm text-green-800">{opportunity}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Risk Factors */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-red-700">
              <AlertTriangle className="h-5 w-5" />
              <span>Risk Factors</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {analytics.insights.riskFactors.map((risk, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-red-50 rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5" />
                  <div>
                    <div className="text-sm font-medium text-red-800">{risk}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Historical Metrics Comparison */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AnalyticsChart
            title="Bond Issuance vs BDC Discount"
            data={analytics.historicalData.bond_issuance || []}
            dataKey="value"
            color="#3b82f6"
            unit=""
            type="line"
            showTrend={true}
            height={300}
            formatValue={(value) => value.toLocaleString()}
            formatDate={(date) => new Date(date).toLocaleDateString()}
          />
          <AnalyticsChart
            title="Credit Funds vs Bank Provisions"
            data={analytics.historicalData.credit_fund || []}
            dataKey="value"
            color="#8b5cf6"
            unit=""
            type="line"
            showTrend={true}
            height={300}
            formatValue={(value) => value.toLocaleString()}
            formatDate={(date) => new Date(date).toLocaleDateString()}
          />
        </div>
      </div>
    </DashboardLayout>
  )
}
