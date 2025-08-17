import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine, Brush } from 'recharts'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { TrendingUp, TrendingDown, Activity, ZoomIn, RotateCcw, Download } from 'lucide-react'

interface DataPoint {
  timestamp: string
  [key: string]: string | number
}

interface TooltipProps {
  active?: boolean
  payload?: Array<{
    value: number
    dataKey: string
    payload: DataPoint
  }>
  label?: string
}

interface ZoomState {
  left: string
  right: string
  refAreaLeft: string
  refAreaRight: string
}

interface AnalyticsChartProps {
  title: string
  data: DataPoint[]
  dataKey: string
  color?: string
  unit?: string
  type?: 'line' | 'area' | 'bar'
  showTrend?: boolean
  showGrid?: boolean
  showLegend?: boolean
  height?: number
  dangerThreshold?: number
  warningThreshold?: number
  formatValue?: (value: number) => string
  formatDate?: (date: string) => string
  enableZoom?: boolean
  enableBrush?: boolean
  enableDrillDown?: boolean
  onDrillDown?: (data: DataPoint) => void
  filteredData?: DataPoint[]
  showFilteredData?: boolean
}

export function AnalyticsChart({
  title,
  data,
  dataKey,
  color = '#3b82f6',
  unit = '',
  type = 'line',
  showTrend = true,
  showGrid = true,
  showLegend = false,
  height = 300,
  dangerThreshold,
  warningThreshold,
  formatValue,
  formatDate,
  enableZoom = false,
  enableBrush = false,
  enableDrillDown = false,
  onDrillDown: _onDrillDown,
  filteredData,
  showFilteredData = false
}: AnalyticsChartProps) {
  const [zoomState, setZoomState] = useState<ZoomState>({ left: 'dataMin', right: 'dataMax', refAreaLeft: '', refAreaRight: '' })
  const [isZoomed, setIsZoomed] = useState(false)
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-48 text-gray-500">
            No data available
          </div>
        </CardContent>
      </Card>
    )
  }

  // Format data for display
  const formatData = (data: DataPoint[]) => {
    return data.map(item => ({
      ...item,
      formattedDate: formatDate ? formatDate(item.timestamp) : new Date(item.timestamp).toLocaleDateString(),
      formattedValue: formatValue ? formatValue(Number(item[dataKey])) : `${Number(item[dataKey]).toLocaleString()}${unit}`
    }))
  }

  // Use filtered data if available and enabled, otherwise use original data
  const displayData = showFilteredData && filteredData ? filteredData : data
  const formattedData = formatData(displayData)

  // Calculate trend
  const calculateTrend = () => {
    if (displayData.length < 2) return { direction: 'stable', percentage: 0 }
    
    const firstValue = Number(displayData[0][dataKey])
    const lastValue = Number(displayData[displayData.length - 1][dataKey])
    const percentage = ((lastValue - firstValue) / firstValue) * 100
    
    return {
      direction: percentage > 5 ? 'up' : percentage < -5 ? 'down' : 'stable',
      percentage: Math.abs(percentage)
    }
  }

  const trend = calculateTrend()

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{label}</p>
          {payload.map((entry, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toLocaleString()}{unit}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  // Custom axis tick
  const CustomAxisTick = ({ x, y, payload }: { x: number; y: number; payload: { value: string } }) => {
    return (
      <g transform={`translate(${x},${y})`}>
        <text x={0} y={0} dy={16} textAnchor="middle" fill="#666" fontSize={12}>
          {payload.value}
        </text>
      </g>
    )
  }

  const handleZoom = (nextState: { left: string; right: string }) => {
    const { left, right } = nextState
    setZoomState({ left, right, refAreaLeft: '', refAreaRight: '' })
    setIsZoomed(true)
  }

  const handleBrushChange = (_brushData: { startIndex: number; endIndex: number } | null) => {
    // Brush functionality can be implemented here if needed
  }

  const resetZoom = () => {
    setZoomState({ left: 'dataMin', right: 'dataMax', refAreaLeft: '', refAreaRight: '' })
    setIsZoomed(false)
  }

  const exportChart = () => {
    const canvas = document.querySelector(`canvas[data-testid="${title}"]`) as HTMLCanvasElement
    if (canvas) {
      const link = document.createElement('a')
      link.download = `${title.replace(/\s+/g, '_')}.png`
      link.href = canvas.toDataURL()
      link.click()
    }
  }

  const renderChart = () => {
    const commonProps = {
      data: formattedData,
      margin: { top: 20, right: 30, left: 20, bottom: 20 }
    }

    switch (type) {
      case 'area':
        return (
          <AreaChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
            <XAxis 
              dataKey="formattedDate" 
              tick={<CustomAxisTick />}
              interval="preserveStartEnd"
              domain={[zoomState.left, zoomState.right]}
            />
            <YAxis 
              tickFormatter={(value) => `${value.toLocaleString()}${unit}`}
              width={80}
            />
            <Tooltip content={<CustomTooltip />} />
            {showLegend && <Legend />}
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              fill={color}
              fillOpacity={0.3}
              strokeWidth={2}
            />
            {dangerThreshold && (
              <ReferenceLine
                y={dangerThreshold}
                stroke="#ef4444"
                strokeDasharray="3 3"
                label={{ value: 'Danger', position: 'insideTopRight' }}
              />
            )}
            {warningThreshold && (
              <ReferenceLine
                y={warningThreshold}
                stroke="#f59e0b"
                strokeDasharray="3 3"
                label={{ value: 'Warning', position: 'insideTopRight' }}
              />
            )}
            {enableZoom && (
              <Brush 
                dataKey="formattedDate" 
                height={30} 
                stroke={color}
                onChange={handleBrushChange}
              />
            )}
          </AreaChart>
        )

      case 'bar':
        return (
          <BarChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
            <XAxis 
              dataKey="formattedDate" 
              tick={<CustomAxisTick />}
              interval="preserveStartEnd"
              domain={[zoomState.left, zoomState.right]}
            />
            <YAxis 
              tickFormatter={(value) => `${value.toLocaleString()}${unit}`}
              width={80}
            />
            <Tooltip content={<CustomTooltip />} />
            {showLegend && <Legend />}
            <Bar
              dataKey={dataKey}
              fill={color}
              radius={[4, 4, 0, 0]}
            />
            {dangerThreshold && (
              <ReferenceLine
                y={dangerThreshold}
                stroke="#ef4444"
                strokeDasharray="3 3"
                label={{ value: 'Danger', position: 'insideTopRight' }}
              />
            )}
            {warningThreshold && (
              <ReferenceLine
                y={warningThreshold}
                stroke="#f59e0b"
                strokeDasharray="3 3"
                label={{ value: 'Warning', position: 'insideTopRight' }}
              />
            )}
            {enableZoom && (
              <Brush 
                dataKey="formattedDate" 
                height={30} 
                stroke={color}
                onChange={handleBrushChange}
              />
            )}
          </BarChart>
        )

      default: // line
        return (
          <LineChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
            <XAxis 
              dataKey="formattedDate" 
              tick={<CustomAxisTick />}
              interval="preserveStartEnd"
              domain={[zoomState.left, zoomState.right]}
            />
            <YAxis 
              tickFormatter={(value) => `${value.toLocaleString()}${unit}`}
              width={80}
            />
            <Tooltip content={<CustomTooltip />} />
            {showLegend && <Legend />}
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={3}
              dot={{ fill: color, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: color, strokeWidth: 2 }}
            />
            {dangerThreshold && (
              <ReferenceLine
                y={dangerThreshold}
                stroke="#ef4444"
                strokeDasharray="3 3"
                label={{ value: 'Danger', position: 'insideTopRight' }}
              />
            )}
            {warningThreshold && (
              <ReferenceLine
                y={warningThreshold}
                stroke="#f59e0b"
                strokeDasharray="3 3"
                label={{ value: 'Warning', position: 'insideTopRight' }}
              />
            )}
            {enableZoom && (
              <Brush 
                dataKey="formattedDate" 
                height={30} 
                stroke={color}
                onChange={handleBrushChange}
              />
            )}
          </LineChart>
        )
    }
  }

  const getTrendIcon = () => {
    switch (trend.direction) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-600" />
      default:
        return <Activity className="h-4 w-4 text-gray-600" />
    }
  }

  const getTrendColor = () => {
    switch (trend.direction) {
      case 'up':
        return 'text-green-600'
      case 'down':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{title}</CardTitle>
          <div className="flex items-center space-x-2">
            {showTrend && (
              <div className="flex items-center space-x-2">
                {getTrendIcon()}
                <Badge variant="outline" className={getTrendColor()}>
                  {trend.direction === 'up' ? '+' : trend.direction === 'down' ? '-' : ''}
                  {trend.percentage.toFixed(1)}%
                </Badge>
              </div>
            )}
            {(enableZoom || enableDrillDown) && (
              <div className="flex items-center space-x-1">
                {enableZoom && (
                  <>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={resetZoom}
                      disabled={!isZoomed}
                      title="Reset Zoom"
                    >
                      <RotateCcw className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={exportChart}
                      title="Export Chart"
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </>
                )}
                {enableDrillDown && onDrillDown && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDrillDown(displayData)}
                    title="Drill Down"
                  >
                    <ZoomIn className="h-4 w-4" />
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          {renderChart()}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
