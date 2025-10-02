import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { HistoricalData } from '@/types/dashboard'

interface MetricChartProps {
  title: string
  data: HistoricalData[]
  dataKey: string
  color?: string
  unit?: string
  type?: 'line' | 'area'
}

export function MetricChart({ 
  title, 
  data, 
  dataKey, 
  color = '#3b82f6', 
  unit = '',
  type = 'line' 
}: MetricChartProps) {
  const formatValue = (value: number) => {
    if (unit === 'currency') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        notation: 'compact',
        maximumFractionDigits: 1
      }).format(value)
    }
    if (unit === 'percentage' || unit === 'percent') {
      return `${value.toFixed(2)}%`
    }
    return value.toLocaleString()
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    })
  }

  const chartData = data.map(item => ({
    ...item,
    timestamp: formatDate(item.timestamp),
    [dataKey]: item.value
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            {type === 'area' ? (
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="timestamp" 
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis 
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={formatValue}
                />
                <Tooltip 
                  formatter={(value: number) => [formatValue(value), title]}
                  labelStyle={{ color: '#374151' }}
                />
                <Area
                  type="monotone"
                  dataKey={dataKey}
                  stroke={color}
                  fill={color}
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              </AreaChart>
            ) : (
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="timestamp" 
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis 
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={formatValue}
                />
                <Tooltip 
                  formatter={(value: number) => [formatValue(value), title]}
                  labelStyle={{ color: '#374151' }}
                />
                <Line
                  type="monotone"
                  dataKey={dataKey}
                  stroke={color}
                  strokeWidth={2}
                  dot={{ fill: color, strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}