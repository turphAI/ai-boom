import React from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { X } from 'lucide-react'

interface DrillDownModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  data: any[]
  dataKey: string
  color: string
  unit: string
  type: 'line' | 'area' | 'bar'
}

export function DrillDownModal({
  isOpen,
  onClose,
  title,
  data,
  dataKey,
  color,
  unit,
  type
}: DrillDownModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>{title}</span>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Simple chart representation */}
          <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-700 mb-2">Chart Preview</div>
              <div className="text-sm text-gray-500">
                {data.length} data points • {type} chart • {color}
              </div>
            </div>
          </div>
          
          {/* Data table */}
          <div className="max-h-64 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-gray-700">Name</th>
                  <th className="px-4 py-2 text-right font-medium text-gray-700">Value</th>
                  <th className="px-4 py-2 text-right font-medium text-gray-700">Percentage</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item, index) => (
                  <tr key={index} className="border-b border-gray-100">
                    <td className="px-4 py-2 text-gray-900">
                      {item.name || item.asset || item.strategy || item.region || item.sector || item.type || item.duration || item.size || item.ticker || `Item ${index + 1}`}
                    </td>
                    <td className="px-4 py-2 text-right text-gray-900">
                      {typeof item[dataKey] === 'number' ? item[dataKey].toFixed(2) : item[dataKey]}{unit}
                    </td>
                    <td className="px-4 py-2 text-right text-gray-500">
                      {item.percentage ? `${item.percentage.toFixed(1)}%` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
