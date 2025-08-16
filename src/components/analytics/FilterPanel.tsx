import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Filter, ChevronLeft, ChevronRight, X, RotateCcw } from 'lucide-react'
import { DateRangeFilter } from './DateRangeFilter'
import { MetricFilter } from './MetricFilter'

interface FilterPanelProps {
  isOpen: boolean
  onToggle: () => void
  onDateRangeChange: (startDate: Date, endDate: Date) => void
  availableMetrics: string[]
  selectedMetrics: string[]
  onMetricsChange: (metrics: string[]) => void
  onResetFilters: () => void
  activeFiltersCount: number
}

export function FilterPanel({
  isOpen,
  onToggle,
  onDateRangeChange,
  availableMetrics,
  selectedMetrics,
  onMetricsChange,
  onResetFilters,
  activeFiltersCount
}: FilterPanelProps) {
  return (
    <div className="relative">
      {/* Toggle Button */}
      <Button
        variant="outline"
        size="sm"
        onClick={onToggle}
        className="fixed top-4 right-4 z-50 flex items-center gap-2"
      >
        <Filter className="h-4 w-4" />
        Filters
        {activeFiltersCount > 0 && (
          <Badge variant="secondary" className="ml-1">
            {activeFiltersCount}
          </Badge>
        )}
        {isOpen ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
      </Button>

      {/* Filter Panel */}
      {isOpen && (
        <div className="fixed top-16 right-4 w-80 bg-white border rounded-lg shadow-lg z-40 max-h-[calc(100vh-6rem)] overflow-y-auto">
          <Card className="border-0 shadow-none">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <Filter className="h-5 w-5" />
                  Filters
                </CardTitle>
                <div className="flex items-center gap-2">
                  {activeFiltersCount > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={onResetFilters}
                      className="h-8 px-2 text-xs"
                    >
                      <RotateCcw className="h-3 w-3 mr-1" />
                      Reset
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onToggle}
                    className="h-8 w-8 p-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Date Range Filter */}
              <DateRangeFilter
                onDateRangeChange={onDateRangeChange}
                className="border-0 shadow-none"
              />

              {/* Metric Filter */}
              <MetricFilter
                availableMetrics={availableMetrics}
                selectedMetrics={selectedMetrics}
                onMetricsChange={onMetricsChange}
                className="border-0 shadow-none"
              />

              {/* Active Filters Summary */}
              {activeFiltersCount > 0 && (
                <div className="pt-4 border-t">
                  <div className="text-sm font-medium text-gray-700 mb-2">
                    Active Filters ({activeFiltersCount})
                  </div>
                  <div className="text-xs text-gray-500">
                    • Date range filter applied
                    {selectedMetrics.length > 0 && (
                      <div>• {selectedMetrics.length} metrics selected</div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
