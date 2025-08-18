import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Download, ZoomIn, ZoomOut, RotateCcw, Target } from 'lucide-react'

interface BubbleData {
  x: number
  y: number
  size: number
  label?: string
  category?: string
  color?: string
}

interface BubbleChartProps {
  title: string
  data: BubbleData[]
  xLabel: string
  yLabel: string
  sizeLabel: string
  height?: number
  className?: string
  showLegend?: boolean
}

export function BubbleChart({ 
  title, 
  data, 
  xLabel, 
  yLabel, 
  sizeLabel, 
  height = 400, 
  className,
  showLegend = true
}: BubbleChartProps) {
  const [isZoomed, setIsZoomed] = useState(false)
  const [selectedBubble, setSelectedBubble] = useState<BubbleData | null>(null)

  // Calculate min/max for scaling
  const minX = Math.min(...data.map(d => d.x))
  const maxX = Math.max(...data.map(d => d.x))
  const minY = Math.min(...data.map(d => d.y))
  const maxY = Math.max(...data.map(d => d.y))
  const minSize = Math.min(...data.map(d => d.size))
  const maxSize = Math.max(...data.map(d => d.size))

  const scaleX = (x: number) => ((x - minX) / (maxX - minX)) * 100
  const scaleY = (y: number) => 100 - ((y - minY) / (maxY - minY)) * 100
  const scaleSize = (size: number) => {
    const normalized = (size - minSize) / (maxSize - minSize)
    return Math.max(8, Math.min(40, 8 + normalized * 32)) // Min 8px, max 40px
  }

  const getBubbleColor = (bubble: BubbleData) => {
    if (bubble.color) return bubble.color
    if (bubble.category) {
      const colors = [
        '#3b82f6', '#ef4444', '#10b981', '#f59e0b', 
        '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'
      ]
      const index = bubble.category.charCodeAt(0) % colors.length
      return colors[index]
    }
    const normalized = (bubble.size - minSize) / (maxSize - minSize)
    if (normalized > 0.7) return '#ef4444'
    if (normalized > 0.4) return '#f59e0b'
    return '#3b82f6'
  }

  const categories = Array.from(new Set(data.map(d => d.category).filter(Boolean)))

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

    data.forEach(bubble => {
      const x = (bubble.x - minX) / (maxX - minX) * canvas.width
      const y = canvas.height - (bubble.y - minY) / (maxY - minY) * canvas.height
      const radius = scaleSize(bubble.size)
      
      ctx.fillStyle = getBubbleColor(bubble)
      ctx.globalAlpha = 0.7
      ctx.beginPath()
      ctx.arc(x, y, radius, 0, 2 * Math.PI)
      ctx.fill()
      
      ctx.globalAlpha = 1
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 2
      ctx.stroke()
    })

    ctx.fillStyle = '#000000'
    ctx.font = '16px Arial'
    ctx.fillText(title, 20, 30)
    ctx.font = '12px Arial'
    ctx.fillText(`${xLabel} vs ${yLabel} (${sizeLabel})`, 20, 50)

    const link = document.createElement('a')
    link.download = `${title.replace(/\s+/g, '_')}_bubble.png`
    link.href = canvas.toDataURL()
    link.click()
  }

  const resetZoom = () => {
    setIsZoomed(false)
    setSelectedBubble(null)
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-lg font-semibold">{title}</CardTitle>
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
              <text x="50%" y="98%" textAnchor="middle" className="text-xs fill-gray-600">{xLabel}</text>
              <text x="2%" y="50%" textAnchor="middle" className="text-xs fill-gray-600" transform="rotate(-90, 2, 50)">{yLabel}</text>
            </svg>

            {data.map((bubble, index) => {
              const size = scaleSize(bubble.size)
              const color = getBubbleColor(bubble)
              return (
                <div
                  key={index}
                  className="absolute cursor-pointer hover:scale-110 transition-transform"
                  style={{ left: `${scaleX(bubble.x)}%`, top: `${scaleY(bubble.y)}%`, transform: 'translate(-50%, -50%)' }}
                  onClick={() => setSelectedBubble(bubble)}
                  title={`${xLabel}: ${bubble.x.toFixed(2)}, ${yLabel}: ${bubble.y.toFixed(2)}, ${sizeLabel}: ${bubble.size.toFixed(2)}`}
                >
                  <div className="rounded-full border-2 border-white shadow-lg" style={{ width: `${size}px`, height: `${size}px`, backgroundColor: color, opacity: 0.8 }} />
                </div>
              )
            })}

            {selectedBubble && (
              <div className="absolute" style={{ left: `${scaleX(selectedBubble.x)}%`, top: `${scaleY(selectedBubble.y)}%`, transform: 'translate(-50%, -50%)' }}>
                <div className="rounded-full border-4 border-red-500 shadow-lg animate-pulse" style={{ width: `${scaleSize(selectedBubble.size) + 8}px`, height: `${scaleSize(selectedBubble.size) + 8}px` }} />
              </div>
            )}
          </div>

          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between"><span className="text-sm font-medium text-gray-600">Data Points:</span><Badge variant="outline">{data.length}</Badge></div>
              <div className="flex items-center justify-between"><span className="text-sm font-medium text-gray-600">Size Range:</span><Badge variant="outline">{minSize.toFixed(2)} - {maxSize.toFixed(2)}</Badge></div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between"><span className="text-sm font-medium text-gray-600">X Range:</span><Badge variant="outline">{minX.toFixed(2)} - {maxX.toFixed(2)}</Badge></div>
              <div className="flex items-center justify-between"><span className="text-sm font-medium text-gray-600">Y Range:</span><Badge variant="outline">{minY.toFixed(2)} - {maxY.toFixed(2)}</Badge></div>
            </div>
          </div>

          {showLegend && categories.length > 0 && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <div className="text-sm font-medium text-gray-700 mb-2">Categories:</div>
              <div className="flex flex-wrap gap-2">
                {categories.map((category) => {
                  const sampleData = data.find(d => d.category === category)
                  const color = sampleData ? getBubbleColor(sampleData) : '#3b82f6'
                  return (
                    <div key={category} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                      <span className="text-xs text-gray-600">{category}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {selectedBubble && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2"><Target className="h-4 w-4 text-red-500" /><span className="text-sm font-medium">Selected Bubble</span></div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-gray-600">{xLabel}:</span><span className="ml-1 font-medium">{selectedBubble.x.toFixed(2)}</span></div>
                <div><span className="text-gray-600">{yLabel}:</span><span className="ml-1 font-medium">{selectedBubble.y.toFixed(2)}</span></div>
                <div><span className="text-gray-600">{sizeLabel}:</span><span className="ml-1 font-medium">{selectedBubble.size.toFixed(2)}</span></div>
                {selectedBubble.label && (<div><span className="text-gray-600">Label:</span><span className="ml-1 font-medium">{selectedBubble.label}</span></div>)}
                {selectedBubble.category && (<div className="col-span-2"><span className="text-gray-600">Category:</span><span className="ml-1 font-medium">{selectedBubble.category}</span></div>)}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}


