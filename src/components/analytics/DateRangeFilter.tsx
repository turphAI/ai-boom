import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Calendar, ChevronDown, ChevronUp } from 'lucide-react'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'

interface DateRangeFilterProps {
  onDateRangeChange: (startDate: Date, endDate: Date) => void
  className?: string
}

const PRESET_RANGES = [
  { label: 'Last 7 Days', days: 7 },
  { label: 'Last 30 Days', days: 30 },
  { label: 'Last 90 Days', days: 90 },
  { label: 'Last 6 Months', days: 180 },
  { label: 'Last Year', days: 365 },
  { label: 'Last 2 Years', days: 730 },
  { label: 'All Time', days: 0 }
]

export function DateRangeFilter({ onDateRangeChange, className }: DateRangeFilterProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [selectedRange, setSelectedRange] = useState('Last 90 Days')
  const [customStartDate, setCustomStartDate] = useState('')
  const [customEndDate, setCustomEndDate] = useState('')

  const handlePresetSelect = (label: string, days: number) => {
    setSelectedRange(label)
    const endDate = new Date()
    const startDate = new Date()
    if (days > 0) {
      startDate.setDate(endDate.getDate() - days)
    } else {
      // All time - set to a reasonable start date
      startDate.setFullYear(2020, 0, 1)
    }
    onDateRangeChange(startDate, endDate)
  }

  const handleCustomDateSubmit = () => {
    if (customStartDate && customEndDate) {
      const startDate = new Date(customStartDate)
      const endDate = new Date(customEndDate)
      if (startDate <= endDate) {
        setSelectedRange('Custom Range')
        onDateRangeChange(startDate, endDate)
      }
    }
  }

  const formatDateRange = (startDate: Date, endDate: Date) => {
    return `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Calendar className="h-4 w-4" />
          Date Range Filter
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Preset Ranges */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-600">Quick Select</label>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="w-full justify-between">
                {selectedRange}
                <ChevronDown className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-full">
              {PRESET_RANGES.map((range) => (
                <DropdownMenuItem
                  key={range.label}
                  onClick={() => handlePresetSelect(range.label, range.days)}
                >
                  {range.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Custom Date Range */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-gray-600">Custom Range</label>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-6 px-2"
            >
              {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </Button>
          </div>
          
          {isExpanded && (
            <div className="space-y-2 p-3 bg-gray-50 rounded-md">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs text-gray-500">Start Date</label>
                  <input
                    type="date"
                    value={customStartDate}
                    onChange={(e) => setCustomStartDate(e.target.value)}
                    className="w-full text-xs p-2 border rounded"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">End Date</label>
                  <input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                    className="w-full text-xs p-2 border rounded"
                  />
                </div>
              </div>
              <Button
                size="sm"
                onClick={handleCustomDateSubmit}
                disabled={!customStartDate || !customEndDate}
                className="w-full"
              >
                Apply Custom Range
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
