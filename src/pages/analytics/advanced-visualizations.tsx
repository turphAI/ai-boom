import React, { useState, useEffect } from 'react'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { HeatmapChart } from '@/components/analytics/HeatmapChart'
import { ScatterPlotChart } from '@/components/analytics/ScatterPlotChart'
import { BubbleChart } from '@/components/analytics/BubbleChart'
import { PredictiveChart } from '@/components/analytics/PredictiveChart'
// import { mockAnalyticsService } from '@/lib/services/mock-analytics-service'
import { BarChart3, TrendingUp, Target, Zap } from 'lucide-react'

export default function AdvancedVisualizations() {
  const [heatmapData, setHeatmapData] = useState<any[]>([])
  const [scatterData, setScatterData] = useState<any[]>([])
  const [bubbleData, setBubbleData] = useState<any[]>([])
  const [predictiveData, setPredictiveData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadData = () => {
      // setHeatmapData(mockAnalyticsService.generateHeatmapData())
      // setScatterData(mockAnalyticsService.generateScatterData())
      // setBubbleData(mockAnalyticsService.generateBubbleData())
      // setPredictiveData(mockAnalyticsService.generatePredictiveData())
      setIsLoading(false)
    }

    loadData()
  }, [])

  const refreshData = () => {
    setIsLoading(true)
    setTimeout(() => {
      // setHeatmapData(mockAnalyticsService.generateHeatmapData())
      // setScatterData(mockAnalyticsService.generateScatterData())
      // setBubbleData(mockAnalyticsService.generateBubbleData())
      // setPredictiveData(mockAnalyticsService.generatePredictiveData())
      setIsLoading(false)
    }, 500)
  }

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading advanced visualizations...</p>
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
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Advanced Visualizations</h1>
            <p className="text-gray-600 mt-2">
              Interactive charts and predictive analytics for deep market analysis
            </p>
          </div>
          <Button onClick={refreshData} variant="outline">
            <Zap className="h-4 w-4 mr-2" />
            Refresh Data
          </Button>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Correlation Analysis</CardTitle>
              <BarChart3 className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">4×4 Matrix</div>
              <p className="text-xs text-muted-foreground">
                Inter-metric correlations
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Scatter Analysis</CardTitle>
              <Target className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">50 Points</div>
              <p className="text-xs text-muted-foreground">
                Relationship patterns
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Bubble Analysis</CardTitle>
              <TrendingUp className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">30 Entities</div>
              <p className="text-xs text-muted-foreground">
                Multi-dimensional data
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Predictive Models</CardTitle>
              <TrendingUp className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">24 Periods</div>
              <p className="text-xs text-muted-foreground">
                Future forecasting
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Heatmap Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Correlation Heatmap Analysis
            </CardTitle>
            <p className="text-sm text-gray-600">
              Interactive correlation matrix showing relationships between key metrics. 
              Hover over cells to see detailed correlation values and strength indicators.
            </p>
          </CardHeader>
          <CardContent>
            <HeatmapChart
              title="Metric Correlation Matrix"
              data={heatmapData}
              xAxis={['bond_issuance', 'bdc_discount', 'credit_fund', 'bank_provision']}
              yAxis={['bond_issuance', 'bdc_discount', 'credit_fund', 'bank_provision']}
              height={400}
            />
          </CardContent>
        </Card>

        {/* Scatter Plot */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Scatter Plot Analysis
            </CardTitle>
            <p className="text-sm text-gray-600">
              Scatter plot showing relationship between two variables with trend line, 
              correlation statistics, and interactive point selection.
            </p>
          </CardHeader>
          <CardContent>
            <ScatterPlotChart
              title="Market Relationship Analysis"
              data={scatterData}
              xLabel="Market Cap (M)"
              yLabel="Revenue Growth (%)"
              height={400}
              showTrendLine={true}
            />
          </CardContent>
        </Card>

        {/* Bubble Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Bubble Chart Analysis
            </CardTitle>
            <p className="text-sm text-gray-600">
              Multi-dimensional bubble chart showing companies by market position, 
              with bubble size representing market cap and color indicating sector.
            </p>
          </CardHeader>
          <CardContent>
            <BubbleChart
              title="Company Market Analysis"
              data={bubbleData}
              xLabel="Market Share (%)"
              yLabel="Growth Rate (%)"
              sizeLabel="Market Cap (B)"
              height={400}
              showLegend={true}
            />
          </CardContent>
        </Card>

        {/* Predictive Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Predictive Analytics
            </CardTitle>
            <p className="text-sm text-gray-600">
              Time series analysis with linear regression prediction, confidence intervals, 
              and trend forecasting for the next 6 periods.
            </p>
          </CardHeader>
          <CardContent>
            <PredictiveChart
              title="Market Trend Prediction"
              data={predictiveData}
              dataKey="value"
              color="#3b82f6"
              unit="M"
              height={400}
              showPrediction={true}
              predictionPeriods={6}
            />
          </CardContent>
        </Card>

        {/* Features Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Advanced Features</CardTitle>
            <p className="text-sm text-gray-600">
              Interactive capabilities and analytical tools available in these visualizations
            </p>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Interactive Controls</h4>
                <div className="space-y-1">
                  <Badge variant="outline" className="text-xs">Zoom & Pan</Badge>
                  <Badge variant="outline" className="text-xs">Point Selection</Badge>
                  <Badge variant="outline" className="text-xs">Export to PNG</Badge>
                </div>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Statistical Analysis</h4>
                <div className="space-y-1">
                  <Badge variant="outline" className="text-xs">Correlation Matrix</Badge>
                  <Badge variant="outline" className="text-xs">R-squared Values</Badge>
                  <Badge variant="outline" className="text-xs">Trend Lines</Badge>
                </div>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Predictive Features</h4>
                <div className="space-y-1">
                  <Badge variant="outline" className="text-xs">Linear Regression</Badge>
                  <Badge variant="outline" className="text-xs">Confidence Intervals</Badge>
                  <Badge variant="outline" className="text-xs">Trend Forecasting</Badge>
                </div>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Data Visualization</h4>
                <div className="space-y-1">
                  <Badge variant="outline" className="text-xs">Color-coded Intensity</Badge>
                  <Badge variant="outline" className="text-xs">Size-based Encoding</Badge>
                  <Badge variant="outline" className="text-xs">Category Legends</Badge>
                </div>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Real-time Features</h4>
                <div className="space-y-1">
                  <Badge variant="outline" className="text-xs">Live Data Updates</Badge>
                  <Badge variant="outline" className="text-xs">Dynamic Refreshing</Badge>
                  <Badge variant="outline" className="text-xs">Interactive Tooltips</Badge>
                </div>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Export & Sharing</h4>
                <div className="space-y-1">
                  <Badge variant="outline" className="text-xs">High-res PNG Export</Badge>
                  <Badge variant="outline" className="text-xs">Chart Embedding</Badge>
                  <Badge variant="outline" className="text-xs">Data Export</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
