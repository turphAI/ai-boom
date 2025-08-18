import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Download, ZoomIn, ZoomOut, RotateCcw, TrendingUp, TrendingDown, Target } from 'lucide-react'

interface PredictiveData {
  timestamp: string
  value: number
  predicted?: number
  confidence?: number
  trend?: 'up' | 'down' | 'stable'
}

interface PredictiveChartProps {
  title: string
  data: PredictiveData[]
  dataKey: string
  color: string
  unit: string
  height?: number
  className?: string
  showPrediction?: boolean
  predictionPeriods?: number
  confidenceLevel?: number
}

export function PredictiveChart({ 
  title, 
  data, 
  dataKey, 
  color, 
  unit, 
  height = 400, 
  className,
  showPrediction = true,
  predictionPeriods = 6,
  confidenceLevel = 0.95
}: PredictiveChartProps) {
  const [isZoomed, setIsZoomed] = useState(false)
  const [selectedPoint, setSelectedPoint] = useState<PredictiveData | null>(null)

  const calculateRSquared = (slope: number, intercept: number, xValues: number[], yValues: number[]) => {
    const meanY = yValues.reduce((sum, y) => sum + y, 0) / yValues.length
    const ssRes = yValues.reduce((sum, y, i) => {
      const predicted = slope * xValues[i] + intercept
      return sum + Math.pow(y - predicted, 2)
    }, 0)
    const ssTot = yValues.reduce((sum, y) => {
      return sum + Math.pow(y - meanY, 2)
    }, 0)

    return 1 - (ssRes / ssTot)
  }

  const calculatePrediction = () => {
    if (data.length < 3) return null

    const n = data.length
    const xValues = data.map((_, i) => i)
    const yValues = data.map(d => d.value)

    const sumX = xValues.reduce((sum, x) => sum + x, 0)
    const sumY = yValues.reduce((sum, y) => sum + y, 0)
    const sumXY = xValues.reduce((sum, x, i) => sum + x * yValues[i], 0)
    const sumX2 = xValues.reduce((sum, x) => sum + x * x, 0)

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX)
    const intercept = (sumY - slope * sumX) / n

    const predictions = []
    const lastIndex = n - 1

    for (let i = 0; i < predictionPeriods; i++) {
      const futureIndex = lastIndex + i + 1
      const predictedValue = slope * futureIndex + intercept
      const residuals = yValues.map((y, j) => y - (slope * j + intercept))
      const mse = residuals.reduce((sum, r) => sum + r * r, 0) / (n - 2)
      const standardError = Math.sqrt(mse * (1 + 1/n + Math.pow(futureIndex - sumX/n, 2) / (sumX2 - sumX*sumX/n)))
      const tValue = 1.96
      const marginOfError = tValue * standardError
      predictions.push({
        index: futureIndex,
        value: predictedValue,
        lower: predictedValue - marginOfError,
        upper: predictedValue + marginOfError,
        confidence: Math.max(0, 1 - Math.abs(marginOfError / predictedValue))
      })
    }

    return {
      slope,
      intercept,
      predictions,
      rSquared: calculateRSquared(slope, intercept, xValues, yValues)
    }
  }

  const prediction = calculatePrediction()

  const calculateTrend = () => {
    if (!prediction) return 'stable'
    return prediction.slope > 0.01 ? 'up' : prediction.slope < -0.01 ? 'down' : 'stable'
  }

  const trend = calculateTrend()

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleDateString()
  }

  const allValues = [...data.map(d => d.value), ...(prediction?.predictions.map(p => p.value) || [])]
  const minValue = Math.min(...allValues)
  const maxValue = Math.max(...allValues)
  const range = maxValue - minValue

  const scaleValue = (value: number) => {
    return ((value - minValue) / range) * 100
  }

  const exportChart = () => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = 800
    canvas.height = 600

    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 1

    for (let i = 0; i <= 10; i++) {
      const x = (canvas.width * i) / 10
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, canvas.height)
      ctx.stroke()
    }

    for (let i = 0; i <= 10; i++) {
      const y = (canvas.height * i) / 10
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(canvas.width, y)
      ctx.stroke()
    }

    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.beginPath()
    data.forEach((point, i) => {
      const x = (i / (data.length - 1)) * canvas.width * 0.8
      const y = canvas.height - (scaleValue(point.value) / 100) * canvas.height * 0.8
      if (i === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })
    ctx.stroke()

    if (prediction) {
      ctx.strokeStyle = '#ef4444'
      ctx.lineWidth = 2
      ctx.setLineDash([5, 5])
      ctx.beginPath()
      const lastHistoricalX = (data.length - 1) / (data.length - 1) * canvas.width * 0.8
      const lastHistoricalY = canvas.height - (scaleValue(data[data.length - 1].value) / 100) * canvas.height * 0.8
      const firstPredictionX = (data.length / (data.length + predictionPeriods - 1)) * canvas.width * 0.8
      const firstPredictionY = canvas.height - (scaleValue(prediction.predictions[0].value) / 100) * canvas.height * 0.8
      ctx.moveTo(lastHistoricalX, lastHistoricalY)
      ctx.lineTo(firstPredictionX, firstPredictionY)
      prediction.predictions.forEach((pred, i) => {
        const x = ((data.length + i) / (data.length + predictionPeriods - 1)) * canvas.width * 0.8
        const y = canvas.height - (scaleValue(pred.value) / 100) * canvas.height * 0.8
        ctx.lineTo(x, y)
      })
      ctx.stroke()
      ctx.setLineDash([])
    }

    ctx.fillStyle = '#000000'
    ctx.font = '16px Arial'
    ctx.fillText(title, 20, 30)
    ctx.font = '12px Arial'
    if (prediction) {
      ctx.fillText(`R² = ${prediction.rSquared.toFixed(3)}`, 20, 50)
      ctx.fillText(`Trend: ${trend}`, 20, 70)
    }

    const link = document.createElement('a')
    link.download = `${title.replace(/\s+/g, '_')}_predictive.png`
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
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          {title}
          {trend === 'up' && <TrendingUp className="h-4 w-4 text-green-500" />}
          {trend === 'down' && <TrendingDown className="h-4 w-4 text-red-500" />}
        </CardTitle>
        <div className="flex items-center space-x-2">
          {isZoomed && (
            <Button variant="outline" size="sm" onClick={resetZoom} className="h-8 px-2">
              <RotateCcw className="h-3 w-3 mr-1" />
              Reset
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={() => setIsZoomed(!isZoomed)} className="h-8 px-2">
            {isZoomed ? <ZoomOut className="h-3 w-3" /> : <ZoomIn className="h-3 w-3" />}
          </Button>
          <Button variant="outline" size="sm" onClick={exportChart} className="h-8 px-2">
            <Download className="h-3 w-3" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className={`${isZoomed ? 'scale-110 transform' : ''} transition-transform duration-200`}>
          <div className="relative border border-gray-200 rounded-lg bg-white" style={{ height: `${height}px` }}>
            <svg className="absolute inset-0 w-full h-full" style={{ pointerEvents: 'none' }}>
              {Array.from({ length: 11 }, (_, i) => (
                <line key={`v-${i}`} x1={`${(i * 100) / 10}%`} y1="0%" x2={`${(i * 100) / 10}%`} y2="100%" stroke="#e5e7eb" strokeWidth="1" />
              ))}
              {Array.from({ length: 11 }, (_, i) => (
                <line key={`h-${i}`} x1="0%" y1={`${(i * 100) / 10}%`} x2="100%" y2={`${(i * 100) / 10}%`} stroke="#e5e7eb" strokeWidth="1" />
              ))}
              <polyline points={data.map((point, i) => { const x = (i / (data.length - 1)) * 100; const y = 100 - scaleValue(point.value); return `${x},${y}` }).join(' ')} fill="none" stroke={color} strokeWidth="2" />
              {prediction && showPrediction && (
                <polyline points={prediction.predictions.map((pred, i) => { const x = ((data.length + i) / (data.length + predictionPeriods - 1)) * 100; const y = 100 - scaleValue(pred.value); return `${x},${y}` }).join(' ')} fill="none" stroke="#ef4444" strokeWidth="2" strokeDasharray="5,5" />
              )}
              {prediction && showPrediction && (
                <path d={`M ${(data.length / (data.length + predictionPeriods - 1)) * 100},${100 - scaleValue(prediction.predictions[0].upper)} ${prediction.predictions.map((pred, i) => { const x = ((data.length + i) / (data.length + predictionPeriods - 1)) * 100; const y = 100 - scaleValue(pred.upper); return `L ${x},${y}` }).join(' ')} ${prediction.predictions.reverse().map((pred, i) => { const x = ((data.length + predictionPeriods - 1 - i) / (data.length + predictionPeriods - 1)) * 100; const y = 100 - scaleValue(pred.lower); return `L ${x},${y}` }).join(' ')} Z`} fill="#ef4444" opacity="0.1" />
              )}
            </svg>

            {data.map((point, index) => (
              <div key={index} className="absolute w-3 h-3 bg-blue-500 rounded-full cursor-pointer hover:scale-150 transition-transform border-2 border-white" style={{ left: `${(index / (data.length - 1)) * 100}%`, top: `${100 - scaleValue(point.value)}%`, transform: 'translate(-50%, -50%)', backgroundColor: color }} onClick={() => setSelectedPoint(point)} title={`${formatDate(point.timestamp)}: ${point.value.toFixed(2)} ${unit}`} />
            ))}

            {prediction && showPrediction && prediction.predictions.map((pred, index) => (
              <div key={`pred-${index}`} className="absolute w-3 h-3 bg-red-500 rounded-full cursor-pointer hover:scale-150 transition-transform border-2 border-white" style={{ left: `${((data.length + index) / (data.length + predictionPeriods - 1)) * 100}%`, top: `${100 - scaleValue(pred.value)}%`, transform: 'translate(-50%, -50%)' }} title={`Prediction ${index + 1}: ${pred.value.toFixed(2)} ${unit} (${(pred.confidence * 100).toFixed(1)}% confidence)`} />
            ))}

            {selectedPoint && (
              <div className="absolute w-6 h-6 bg-red-500 rounded-full border-2 border-white shadow-lg" style={{ left: `${(data.findIndex(p => p.timestamp === selectedPoint.timestamp) / (data.length - 1)) * 100}%`, top: `${100 - scaleValue(selectedPoint.value)}%`, transform: 'translate(-50%, -50%)' }} />
            )}
          </div>

          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Trend:</span>
                <Badge variant={trend === 'up' ? 'default' : trend === 'down' ? 'destructive' : 'secondary'}>
                  {trend === 'up' ? '↗ Upward' : trend === 'down' ? '↘ Downward' : '→ Stable'}
                </Badge>
              </div>
              {prediction && (<div className="flex items-center justify-between"><span className="text-sm font-medium text-gray-600">R-squared:</span><Badge variant={prediction.rSquared > 0.7 ? 'default' : 'secondary'}>{prediction.rSquared.toFixed(3)}</Badge></div>)}
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between"><span className="text-sm font-medium text-gray-600">Data Points:</span><Badge variant="outline">{data.length}</Badge></div>
              {prediction && (<div className="flex items-center justify-between"><span className="text-sm font-medium text-gray-600">Predictions:</span><Badge variant="outline">{predictionPeriods}</Badge></div>)}
            </div>
          </div>

          {prediction && showPrediction && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2"><Target className="h-4 w-4 text-red-500" /><span className="text-sm font-medium">Prediction Summary</span></div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-gray-600">Next Period:</span><span className="ml-1 font-medium">{prediction.predictions[0].value.toFixed(2)} {unit}</span></div>
                <div><span className="text-gray-600">Confidence:</span><span className="ml-1 font-medium">{(prediction.predictions[0].confidence * 100).toFixed(1)}%</span></div>
                <div><span className="text-gray-600">Final Prediction:</span><span className="ml-1 font-medium">{prediction.predictions[prediction.predictions.length - 1].value.toFixed(2)} {unit}</span></div>
                <div><span className="text-gray-600">Slope:</span><span className="ml-1 font-medium">{prediction.slope.toFixed(3)}</span></div>
              </div>
            </div>
          )}

          {selectedPoint && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2"><Target className="h-4 w-4 text-blue-500" /><span className="text-sm font-medium">Selected Point</span></div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-gray-600">Date:</span><span className="ml-1 font-medium">{formatDate(selectedPoint.timestamp)}</span></div>
                <div><span className="text-gray-600">Value:</span><span className="ml-1 font-medium">{selectedPoint.value.toFixed(2)} {unit}</span></div>
                {selectedPoint.predicted !== undefined && (<div><span className="text-gray-600">Predicted:</span><span className="ml-1 font-medium">{selectedPoint.predicted.toFixed(2)} {unit}</span></div>)}
                {selectedPoint.confidence !== undefined && (<div><span className="text-gray-600">Confidence:</span><span className="ml-1 font-medium">{(selectedPoint.confidence * 100).toFixed(1)}%</span></div>)}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
