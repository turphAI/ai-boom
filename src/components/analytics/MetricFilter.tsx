import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Filter, X, Check } from 'lucide-react'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'

interface MetricFilterProps {
  availableMetrics: string[]
  selectedMetrics: string[]
  onMetricsChange: (metrics: string[]) => void
  className?: string
}

export function MetricFilter({ availableMetrics, selectedMetrics, onMetricsChange, className }: MetricFilterProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const handleMetricToggle = (metric: string) => {
    if (selectedMetrics.includes(metric)) {
      onMetricsChange(selectedMetrics.filter(m => m !== metric))
    } else {
      onMetricsChange([...selectedMetrics, metric])
    }
  }

  const handleSelectAll = () => {
    onMetricsChange(availableMetrics)
  }

  const handleClearAll = () => {
    onMetricsChange([])
  }

  const handleSelectNone = () => {
    onMetricsChange([])
  }

  const getMetricColor = (metric: string) => {
    const colors = {
      'bond_issuance': 'bg-blue-100 text-blue-800',
      'bdc_discount': 'bg-green-100 text-green-800',
      'credit_fund': 'bg-purple-100 text-purple-800',
      'bank_provision': 'bg-red-100 text-red-800',
      'demand_side': 'bg-orange-100 text-orange-800',
      'supply_side': 'bg-indigo-100 text-indigo-800',
      'financing': 'bg-pink-100 text-pink-800',
      'technology': 'bg-cyan-100 text-cyan-800',
      'healthcare': 'bg-emerald-100 text-emerald-800',
      'energy': 'bg-amber-100 text-amber-800',
      'private_credit': 'bg-violet-100 text-violet-800',
      'direct_lending': 'bg-rose-100 text-rose-800',
      'infrastructure': 'bg-slate-100 text-slate-800',
      'commercial_real_estate': 'bg-yellow-100 text-yellow-800',
      'technology_lending': 'bg-sky-100 text-sky-800',
      'consumer_credit': 'bg-lime-100 text-lime-800'
    }
    return colors[metric as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  const formatMetricName = (metric: string) => {
    return metric.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Filter className="h-4 w-4" />
          Metric Filter
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Quick Actions */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSelectAll}
            className="text-xs"
          >
            Select All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearAll}
            className="text-xs"
          >
            Clear All
          </Button>
        </div>

        {/* Selected Metrics */}
        {selectedMetrics.length > 0 && (
          <div className="space-y-2">
            <label className="text-xs font-medium text-gray-600">Selected Metrics</label>
            <div className="flex flex-wrap gap-1">
              {selectedMetrics.map((metric) => (
                <Badge
                  key={metric}
                  variant="secondary"
                  className={`${getMetricColor(metric)} cursor-pointer hover:opacity-80`}
                  onClick={() => handleMetricToggle(metric)}
                >
                  {formatMetricName(metric)}
                  <X className="h-3 w-3 ml-1" />
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Available Metrics */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-gray-600">Available Metrics</label>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-6 px-2"
            >
              {isExpanded ? 'Hide' : 'Show'}
            </Button>
          </div>
          
          {isExpanded && (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {availableMetrics.map((metric) => (
                <div
                  key={metric}
                  className="flex items-center justify-between p-2 rounded-md border cursor-pointer hover:bg-gray-50"
                  onClick={() => handleMetricToggle(metric)}
                >
                  <span className="text-sm">{formatMetricName(metric)}</span>
                  {selectedMetrics.includes(metric) && (
                    <Check className="h-4 w-4 text-green-600" />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Summary */}
        <div className="text-xs text-gray-500">
          {selectedMetrics.length} of {availableMetrics.length} metrics selected
        </div>
      </CardContent>
    </Card>
  )
}
