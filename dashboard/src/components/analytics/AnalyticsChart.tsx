import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface HistoricalData {
  timestamp: string
  value: number
}

interface AnalyticsChartProps {
  data: HistoricalData[]
  dataKey: string
  color?: string
  unit?: string
  height?: number
}

export function AnalyticsChart({
  data,
  dataKey,
  color = '#3b82f6',
  unit = '',
  height = 300
}: AnalyticsChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500">
        No data available
      </div>
    )
  }

  const maxValue = Math.max(...data.map(d => d.value))
  const minValue = Math.min(...data.map(d => d.value))
  const range = maxValue - minValue

  return (
    <div className="relative" style={{ height: `${height}px` }}>
      <svg className="w-full h-full" style={{ pointerEvents: 'none' }}>
        {/* Grid lines */}
        {Array.from({ length: 5 }, (_, i) => (
          <line
            key={`grid-${i}`}
            x1="0%"
            y1={`${(i * 100) / 4}%`}
            x2="100%"
            y2={`${(i * 100) / 4}%`}
            stroke="#e5e7eb"
            strokeWidth="1"
          />
        ))}
        
        {/* Chart line */}
        <polyline
          points={data.map((point, i) => {
            const x = (i / (data.length - 1)) * 100
            const y = 100 - ((point.value - minValue) / range) * 100
            return `${x},${y}`
          }).join(' ')}
          fill="none"
          stroke={color}
          strokeWidth="2"
        />
        
        {/* Data points */}
        {data.map((point, i) => {
          const x = (i / (data.length - 1)) * 100
          const y = 100 - ((point.value - minValue) / range) * 100
          return (
            <circle
              key={i}
              cx={`${x}%`}
              cy={`${y}%`}
              r="3"
              fill={color}
            />
          )
        })}
      </svg>
      
      {/* Y-axis labels */}
      <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-gray-500">
        <span>{maxValue.toFixed(1)}{unit}</span>
        <span>{minValue.toFixed(1)}{unit}</span>
      </div>
    </div>
  )
}
