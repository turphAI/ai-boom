import React from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { X, Calendar, BarChart3 } from 'lucide-react'
import { HistoricalData } from '@/types/dashboard'

interface FilterPanelProps {
  isOpen: boolean
  onClose: () => void
  dateRange: { start: Date; end: Date }
  onDateRangeChange: (range: { start: Date; end: Date }) => void
  selectedMetrics: string[]
  onMetricsChange: (metrics: string[]) => void
  onApplyFilters: (filteredData: HistoricalData[]) => void
  historicalData: HistoricalData[]
}

export function FilterPanel({
  isOpen,
  onClose,
  dateRange,
  onDateRangeChange,
  selectedMetrics,
  onMetricsChange,
  onApplyFilters,
  historicalData
}: FilterPanelProps) {
  const handleApplyFilters = () => {
    // Simple filtering logic - in a real implementation this would be more sophisticated
    const filteredData = historicalData.filter(item => {
      const itemDate = new Date(item.timestamp)
      return itemDate >= dateRange.start && itemDate <= dateRange.end
    })
    onApplyFilters(filteredData)
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              <span>Filter Options</span>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          {/* Date Range */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
              <Calendar className="h-4 w-4" />
              Date Range
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Start Date</label>
                <input
                  type="date"
                  value={dateRange.start.toISOString().split('T')[0]}
                  onChange={(e) => onDateRangeChange({
                    ...dateRange,
                    start: new Date(e.target.value)
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">End Date</label>
                <input
                  type="date"
                  value={dateRange.end.toISOString().split('T')[0]}
                  onChange={(e) => onDateRangeChange({
                    ...dateRange,
                    end: new Date(e.target.value)
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
            </div>
          </div>

          {/* Quick Date Presets */}
          <div className="space-y-2">
            <div className="text-xs text-gray-500">Quick Presets</div>
            <div className="flex flex-wrap gap-2">
              {[
                { label: '7D', days: 7 },
                { label: '30D', days: 30 },
                { label: '90D', days: 90 },
                { label: '1Y', days: 365 }
              ].map((preset) => (
                <Button
                  key={preset.label}
                  variant="outline"
                  size="sm"
                  onClick={() => onDateRangeChange({
                    start: new Date(Date.now() - preset.days * 24 * 60 * 60 * 1000),
                    end: new Date()
                  })}
                  className="text-xs"
                >
                  {preset.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
            <Button onClick={handleApplyFilters} className="flex-1">
              Apply Filters
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
