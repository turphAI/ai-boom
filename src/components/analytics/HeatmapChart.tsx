import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Download, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react'

interface HeatmapData {
  x: string
  y: string
  value: number
  correlation: number
}

interface HeatmapChartProps {
  title: string
  data: HeatmapData[]
  xAxis: string[]
  yAxis: string[]
  height?: number
  className?: string
}

export function HeatmapChart({ title, data, xAxis, yAxis, height = 400, className }: HeatmapChartProps) {
  const [isZoomed, setIsZoomed] = useState(false)

  const getCorrelationColor = (value: number) => {
    const absValue = Math.abs(value)
    if (absValue >= 0.8) return 'bg-red-500'
    if (absValue >= 0.6) return 'bg-orange-500'
    if (absValue >= 0.4) return 'bg-yellow-500'
    if (absValue >= 0.2) return 'bg-blue-500'
    return 'bg-gray-300'
  }

  const getCorrelationStrength = (value: number) => {
    const absValue = Math.abs(value)
    if (absValue >= 0.8) return 'Very Strong'
    if (absValue >= 0.6) return 'Strong'
    if (absValue >= 0.4) return 'Moderate'
    if (absValue >= 0.2) return 'Weak'
    return 'Very Weak'
  }

  const getCorrelationDirection = (value: number) => {
    if (value > 0) return 'Positive'
    if (value < 0) return 'Negative'
    return 'No Correlation'
  }

  const exportChart = () => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = 800
    canvas.height = 600

    // Draw heatmap
    const cellWidth = canvas.width / (xAxis.length + 1)
    const cellHeight = canvas.height / (yAxis.length + 1)

    // Draw axis labels
    ctx.fillStyle = '#000'
    ctx.font = '12px Arial'
    
    // X-axis labels
    xAxis.forEach((label, i) => {
      ctx.save()
      ctx.translate((i + 1) * cellWidth + cellWidth / 2, cellHeight / 2)
      ctx.rotate(-Math.PI / 4)
      ctx.fillText(label, 0, 0)
      ctx.restore()
    })

    // Y-axis labels
    yAxis.forEach((label, i) => {
      ctx.fillText(label, cellWidth / 2, (i + 1) * cellHeight + cellHeight / 2)
    })

    // Draw heatmap cells
    data.forEach((item) => {
      const xIndex = xAxis.indexOf(item.x)
      const yIndex = yAxis.indexOf(item.y)
      
      if (xIndex !== -1 && yIndex !== -1) {
        const x = (xIndex + 1) * cellWidth
        const y = (yIndex + 1) * cellHeight
        
        // Color based on correlation
        const color = getCorrelationColor(item.correlation)
        ctx.fillStyle = color === 'bg-red-500' ? '#ef4444' :
                       color === 'bg-orange-500' ? '#f97316' :
                       color === 'bg-yellow-500' ? '#eab308' :
                       color === 'bg-blue-500' ? '#3b82f6' : '#d1d5db'
        
        ctx.fillRect(x, y, cellWidth, cellHeight)
        
        // Draw value
        ctx.fillStyle = '#000'
        ctx.font = '10px Arial'
        ctx.fillText(item.correlation.toFixed(2), x + cellWidth / 2 - 10, y + cellHeight / 2 + 3)
      }
    })

    // Download
    const link = document.createElement('a')
    link.download = `${title.replace(/\s+/g, '_')}_heatmap.png`
    link.href = canvas.toDataURL()
    link.click()
  }

  const resetZoom = () => {
    setIsZoomed(false)
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-lg font-semibold">{title}</CardTitle>
        <div className="flex items-center space-x-2">
          {isZoomed && (
            <Button
              variant="outline"
              size="sm"
              onClick={resetZoom}
              className="h-8 px-2"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              Reset
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsZoomed(!isZoomed)}
            className="h-8 px-2"
          >
            {isZoomed ? <ZoomOut className="h-3 w-3" /> : <ZoomIn className="h-3 w-3" />}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={exportChart}
            className="h-8 px-2"
          >
            <Download className="h-3 w-3" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className={`${isZoomed ? 'scale-110 transform' : ''} transition-transform duration-200`}>
          <div className="overflow-x-auto">
            <div className="min-w-max">
              {/* Header row with X-axis labels */}
              <div className="flex">
                <div className="w-32 h-8 flex items-center justify-center text-xs font-medium text-gray-600">
                  {/* Empty corner */}
                </div>
                {xAxis.map((label) => (
                  <div
                    key={label}
                    className="w-20 h-8 flex items-center justify-center text-xs font-medium text-gray-600 transform -rotate-45 origin-center"
                  >
                    {label}
                  </div>
                ))}
              </div>

              {/* Heatmap rows */}
              {yAxis.map((yLabel) => (
                <div key={yLabel} className="flex">
                  {/* Y-axis label */}
                  <div className="w-32 h-20 flex items-center justify-center text-xs font-medium text-gray-600 border-r border-gray-200">
                    {yLabel}
                  </div>
                  
                  {/* Heatmap cells */}
                  {xAxis.map((xLabel) => {
                    const cellData = data.find(d => d.x === xLabel && d.y === yLabel)
                    const correlation = cellData?.correlation || 0
                    const color = getCorrelationColor(correlation)
                    const strength = getCorrelationStrength(correlation)
                    const direction = getCorrelationDirection(correlation)

                    return (
                      <div
                        key={`${xLabel}-${yLabel}`}
                        className={`w-20 h-20 border border-gray-200 flex flex-col items-center justify-center relative group cursor-pointer hover:scale-105 transition-transform`}
                        title={`${xLabel} vs ${yLabel}: ${correlation.toFixed(3)} (${strength} ${direction})`}
                      >
                        <div className={`w-12 h-12 rounded ${color} flex items-center justify-center text-white text-xs font-bold`}>
                          {correlation.toFixed(2)}
                        </div>
                        
                        {/* Tooltip */}
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                          <div className="font-medium">{xLabel} vs {yLabel}</div>
                          <div>Correlation: {correlation.toFixed(3)}</div>
                          <div>{strength} {direction}</div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="mt-4 flex items-center justify-center space-x-4">
            <div className="text-xs text-gray-600">Correlation Strength:</div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-red-500 rounded"></div>
              <span className="text-xs">Very Strong (≥0.8)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-orange-500 rounded"></div>
              <span className="text-xs">Strong (≥0.6)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-yellow-500 rounded"></div>
              <span className="text-xs">Moderate (≥0.4)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-blue-500 rounded"></div>
              <span className="text-xs">Weak (≥0.2)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-gray-300 rounded"></div>
              <span className="text-xs">Very Weak (&lt;0.2)</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
