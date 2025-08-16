import React from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { X, TrendingUp, TrendingDown, Activity } from 'lucide-react'
import { AnalyticsChart } from './AnalyticsChart'

interface DrillDownModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  data: any[]
  dataKey: string
  color?: string
  unit?: string
  type?: 'line' | 'area' | 'bar'
}

export function DrillDownModal({
  isOpen,
  onClose,
  title,
  data,
  dataKey,
  color = '#3b82f6',
  unit = '',
  type = 'line'
}: DrillDownModalProps) {
  if (!data || data.length === 0) {
    return null
  }

  // Calculate detailed statistics
  const values = data.map(d => d[dataKey])
  const maxValue = Math.max(...values)
  const minValue = Math.min(...values)
  const avgValue = values.reduce((a, b) => a + b, 0) / values.length
  const latestValue = values[values.length - 1]
  const firstValue = values[0]
  const changePercent = ((latestValue - firstValue) / firstValue) * 100

  const getTrendIcon = () => {
    if (changePercent > 5) return <TrendingUp className="h-4 w-4 text-green-600" />
    if (changePercent < -5) return <TrendingDown className="h-4 w-4 text-red-600" />
    return <Activity className="h-4 w-4 text-gray-600" />
  }

  const getTrendColor = () => {
    if (changePercent > 5) return 'text-green-600'
    if (changePercent < -5) return 'text-red-600'
    return 'text-gray-600'
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="text-xl">Drill-Down Analysis: {title}</DialogTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>
        
        <div className="space-y-6">
          {/* Summary Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-gray-600">Current Value</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">
                  {unit === '%' ? `${latestValue.toFixed(1)}%` : 
                   unit === 'B' ? `$${(latestValue / 1000000000).toFixed(1)}B` :
                   latestValue.toLocaleString()}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-gray-600">Change</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center space-x-2">
                  {getTrendIcon()}
                  <span className={`text-lg font-bold ${getTrendColor()}`}>
                    {changePercent > 0 ? '+' : ''}{changePercent.toFixed(1)}%
                  </span>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-gray-600">Maximum</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-lg font-bold text-gray-900">
                  {unit === '%' ? `${maxValue.toFixed(1)}%` : 
                   unit === 'B' ? `$${(maxValue / 1000000000).toFixed(1)}B` :
                   maxValue.toLocaleString()}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-gray-600">Average</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-lg font-bold text-gray-900">
                  {unit === '%' ? `${avgValue.toFixed(1)}%` : 
                   unit === 'B' ? `$${(avgValue / 1000000000).toFixed(1)}B` :
                   avgValue.toLocaleString()}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Detailed Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <AnalyticsChart
                title=""
                data={data}
                dataKey={dataKey}
                color={color}
                unit={unit}
                type={type}
                showTrend={false}
                height={400}
                enableZoom={true}
                formatValue={(value) => {
                  if (unit === '%') return `${value.toFixed(1)}%`
                  if (unit === 'B') return `$${(value / 1000000000).toFixed(1)}B`
                  return value.toLocaleString()
                }}
                formatDate={(date) => new Date(date).toLocaleDateString()}
              />
            </CardContent>
          </Card>

          {/* Data Table */}
          <Card>
            <CardHeader>
              <CardTitle>Raw Data</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2 font-semibold">Date</th>
                      <th className="text-right p-2 font-semibold">Value</th>
                      <th className="text-right p-2 font-semibold">Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.slice(-20).map((item, index) => {
                      const prevValue = index > 0 ? data[data.length - 21 + index - 1][dataKey] : item[dataKey]
                      const change = item[dataKey] - prevValue
                      const changePercent = ((change / prevValue) * 100)
                      
                      return (
                        <tr key={index} className="border-b hover:bg-gray-50">
                          <td className="p-2">
                            {new Date(item.timestamp).toLocaleDateString()}
                          </td>
                          <td className="p-2 text-right font-medium">
                            {unit === '%' ? `${item[dataKey].toFixed(1)}%` : 
                             unit === 'B' ? `$${(item[dataKey] / 1000000000).toFixed(1)}B` :
                             item[dataKey].toLocaleString()}
                          </td>
                          <td className="p-2 text-right">
                            <Badge 
                              variant="outline" 
                              className={change > 0 ? 'text-green-600 border-green-200' : 
                                        change < 0 ? 'text-red-600 border-red-200' : 
                                        'text-gray-600 border-gray-200'}
                            >
                              {change > 0 ? '+' : ''}{changePercent.toFixed(1)}%
                            </Badge>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  )
}
