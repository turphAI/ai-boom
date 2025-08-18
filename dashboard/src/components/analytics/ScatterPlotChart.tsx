import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Download, ZoomIn, ZoomOut, RotateCcw, Target } from 'lucide-react'

interface ScatterData {
  x: number
  y: number
  label?: string
  category?: string
  size?: number
}

interface ScatterPlotChartProps {
  title: string
  data: ScatterData[]
  xLabel: string
  yLabel: string
  height?: number
  className?: string
  showTrendLine?: boolean
  showRegression?: boolean
}

export function ScatterPlotChart({ 
  title, 
  data, 
  xLabel, 
  yLabel, 
  height = 400, 
  className,
  showTrendLine = true,
  showRegression = false
}: ScatterPlotChartProps) {
  const [isZoomed, setIsZoomed] = useState(false)
  const [selectedPoint, setSelectedPoint] = useState<ScatterData | null>(null)

  // Calculate trend line
  const calculateTrendLine = () => {
    if (data.length < 2) return null

    const n = data.length
    const sumX = data.reduce((sum, point) => sum + point.x, 0)
    const sumY = data.reduce((sum, point) => sum + point.y, 0)
    const sumXY = data.reduce((sum, point) => sum + point.x * point.y, 0)
    const sumX2 = data.reduce((sum, point) => sum + point.x * point.x, 0)

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX)
    const intercept = (sumY - slope * sumX) / n

    const minX = Math.min(...data.map(d => d.x))
    const maxX = Math.max(...data.map(d => d.x))

    return {
      slope,
      intercept,
      start: { x: minX, y: slope * minX + intercept },
      end: { x: maxX, y: slope * maxX + intercept }
    }
  }

  const trendLine = calculateTrendLine()

  // Calculate R-squared
  const calculateRSquared = () => {
    if (!trendLine || data.length < 2) return 0

    const meanY = data.reduce((sum, point) => sum + point.y, 0) / data.length
    const ssRes = data.reduce((sum, point) => {
      const predicted = trendLine.slope * point.x + trendLine.intercept
      return sum + Math.pow(point.y - predicted, 2)
    }, 0)
    const ssTot = data.reduce((sum, point) => {
      return sum + Math.pow(point.y - meanY, 2)
    }, 0)

    return 1 - (ssRes / ssTot)
  }

  const rSquared = calculateRSquared()

  // Calculate correlation
  const calculateCorrelation = () => {
    if (data.length < 2) return 0

    const n = data.length
    const sumX = data.reduce((sum, point) => sum + point.x, 0)
    const sumY = data.reduce((sum, point) => sum + point.y, 0)
    const sumXY = data.reduce((sum, point) => sum + point.x * point.y, 0)
    const sumX2 = data.reduce((sum, point) => sum + point.x * point.x, 0)
    const sumY2 = data.reduce((sum, point) => sum + point.y * point.y, 0)

    const numerator = n * sumXY - sumX * sumY
    const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY))

    return denominator === 0 ? 0 : numerator / denominator
  }

  const correlation = calculateCorrelation()

  // Find min/max for scaling
  const minX = Math.min(...data.map(d => d.x))
  const maxX = Math.max(...data.map(d => d.x))
  const minY = Math.min(...data.map(d => d.y))
  const maxY = Math.max(...data.map(d => d.y))

  const scaleX = (x: number) => ((x - minX) / (maxX - minX)) * 100
  const scaleY = (y: number) => 100 - ((y - minY) / (maxY - minY)) * 100

  const exportChart = () => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = 800
    canvas.height = 600

    // Set background
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Draw grid
    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 1

    // Vertical grid lines
    for (let i = 0; i <= 10; i++) {
      const x = (canvas.width * i) / 10
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, canvas.height)
      ctx.stroke()
    }

    // Horizontal grid lines
    for (let i = 0; i <= 10; i++) {
      const y = (canvas.height * i) / 10
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(canvas.width, y)
      ctx.stroke()
    }

    // Draw trend line
    if (trendLine) {
      ctx.strokeStyle = '#ef4444'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(
        (trendLine.start.x - minX) / (maxX - minX) * canvas.width,
        canvas.height - (trendLine.start.y - minY) / (maxY - minY) * canvas.height
      )
      ctx.lineTo(
        (trendLine.end.x - minX) / (maxX - minX) * canvas.width,
        canvas.height - (trendLine.end.y - minY) / (maxY - minY) * canvas.height
      )
      ctx.stroke()
    }

    // Draw points
    ctx.fillStyle = '#3b82f6'
    data.forEach(point => {
      const x = (point.x - minX) / (maxX - minX) * canvas.width
      const y = canvas.height - (point.y - minY) / (maxY - minY) * canvas.height
      
      ctx.beginPath()
      ctx.arc(x, y, 4, 0, 2 * Math.PI)
      ctx.fill()
    })

    // Draw labels
    ctx.fillStyle = '#000000'
    ctx.font = '16px Arial'
    ctx.fillText(title, 20, 30)
    ctx.font = '12px Arial'
    ctx.fillText(`R² = ${rSquared.toFixed(3)}`, 20, 50)
    ctx.fillText(`Correlation = ${correlation.toFixed(3)}`, 20, 70)

    // Download
    const link = document.createElement('a')
    link.download = `${title.replace(/\s+/g, '_')}_scatter.png`
    link.href = canvas.toDataURL()
    link.click()
  }

  const resetZoom = () => {
    setIsZoomed(false)
    setSelectedPoint(null)
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
          {/* Chart Container */}
          <div 
            className="relative border border-gray-200 rounded-lg bg-white"
            style={{ height: `${height}px` }}
          >
            {/* Grid Lines */}
            <svg className="absolute inset-0 w-full h-full" style={{ pointerEvents: 'none' }}>
              {/* Vertical grid lines */}
              {Array.from({ length: 11 }, (_, i) => (
                <line
                  key={`v-${i}`}
                  x1={`${(i * 100) / 10}%`}
                  y1="0%"
                  x2={`${(i * 100) / 10}%`}
                  y2="100%"
                  stroke="#e5e7eb"
                  strokeWidth="1"
                />
              ))}
              
              {/* Horizontal grid lines */}
              {Array.from({ length: 11 }, (_, i) => (
                <line
                  key={`h-${i}`}
                  x1="0%"
                  y1={`${(i * 100) / 10}%`}
                  x2="100%"
                  y2={`${(i * 100) / 10}%`}
                  stroke="#e5e7eb"
                  strokeWidth="1"
                />
              ))}

              {/* Trend Line */}
              {trendLine && showTrendLine && (
                <line
                  x1={`${scaleX(trendLine.start.x)}%`}
                  y1={`${scaleY(trendLine.start.y)}%`}
                  x2={`${scaleX(trendLine.end.x)}%`}
                  y2={`${scaleY(trendLine.end.y)}%`}
                  stroke="#ef4444"
                  strokeWidth="2"
                  strokeDasharray="5,5"
                />
              )}

              {/* Axis Labels */}
              <text x="50%" y="98%" textAnchor="middle" className="text-xs fill-gray-600">
                {xLabel}
              </text>
              <text x="2%" y="50%" textAnchor="middle" className="text-xs fill-gray-600" transform="rotate(-90, 2, 50)">
                {yLabel}
              </text>
            </svg>

            {/* Data Points */}
            {data.map((point, index) => (
              <div
                key={index}
                className="absolute w-3 h-3 bg-blue-500 rounded-full cursor-pointer hover:scale-150 transition-transform"
                style={{
                  left: `${scaleX(point.x)}%`,
                  top: `${scaleY(point.y)}%`,
                  transform: 'translate(-50%, -50%)'
                }}
                onClick={() => setSelectedPoint(point)}
                title={`${xLabel}: ${point.x.toFixed(2)}, ${yLabel}: ${point.y.toFixed(2)}`}
              />
            ))}

            {/* Selected Point Highlight */}
            {selectedPoint && (
              <div
                className="absolute w-6 h-6 bg-red-500 rounded-full border-2 border-white shadow-lg"
                style={{
                  left: `${scaleX(selectedPoint.x)}%`,
                  top: `${scaleY(selectedPoint.y)}%`,
                  transform: 'translate(-50%, -50%)'
                }}
              />
            )}
          </div>

          {/* Statistics */}
          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Correlation:</span>
                <Badge variant={Math.abs(correlation) > 0.7 ? 'default' : 'secondary'}>
                  {correlation.toFixed(3)}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">R-squared:</span>
                <Badge variant={rSquared > 0.5 ? 'default' : 'secondary'}>
                  {rSquared.toFixed(3)}
                </Badge>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Data Points:</span>
                <Badge variant="outline">{data.length}</Badge>
              </div>
              {trendLine && (
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-600">Slope:</span>
                  <Badge variant="outline">{trendLine.slope.toFixed(3)}</Badge>
                </div>
              )}
            </div>
          </div>

          {/* Selected Point Details */}
          {selectedPoint && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-4 w-4 text-red-500" />
                <span className="text-sm font-medium">Selected Point</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-600">{xLabel}:</span>
                  <span className="ml-1 font-medium">{selectedPoint.x.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-gray-600">{yLabel}:</span>
                  <span className="ml-1 font-medium">{selectedPoint.y.toFixed(2)}</span>
                </div>
                {selectedPoint.label && (
                  <div className="col-span-2">
                    <span className="text-gray-600">Label:</span>
                    <span className="ml-1 font-medium">{selectedPoint.label}</span>
                  </div>
                )}
                {selectedPoint.category && (
                  <div className="col-span-2">
                    <span className="text-gray-600">Category:</span>
                    <span className="ml-1 font-medium">{selectedPoint.category}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}


