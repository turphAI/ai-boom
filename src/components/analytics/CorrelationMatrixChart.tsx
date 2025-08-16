import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface CorrelationMatrixChartProps {
  correlationMatrix: {
    bondIssuance: { bdcDiscount: number; creditFunds: number; bankProvisions: number }
    bdcDiscount: { bondIssuance: number; creditFunds: number; bankProvisions: number }
    creditFunds: { bondIssuance: number; bdcDiscount: number; bankProvisions: number }
    bankProvisions: { bondIssuance: number; bdcDiscount: number; creditFunds: number }
  }
}

export function CorrelationMatrixChart({ correlationMatrix }: CorrelationMatrixChartProps) {
  const metrics = [
    { key: 'bondIssuance', name: 'Bond Issuance', color: '#3b82f6' },
    { key: 'bdcDiscount', name: 'BDC Discount', color: '#10b981' },
    { key: 'creditFunds', name: 'Credit Funds', color: '#8b5cf6' },
    { key: 'bankProvisions', name: 'Bank Provisions', color: '#ef4444' }
  ]

  const getCorrelationStrength = (correlation: number) => {
    const abs = Math.abs(correlation)
    if (abs > 0.7) return 'Strong'
    if (abs > 0.4) return 'Moderate'
    if (abs > 0.2) return 'Weak'
    return 'None'
  }

  const getCorrelationColor = (correlation: number) => {
    const abs = Math.abs(correlation)
    if (abs > 0.7) return 'bg-green-100 text-green-800 border-green-200'
    if (abs > 0.4) return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    if (abs > 0.2) return 'bg-blue-100 text-blue-800 border-blue-200'
    return 'bg-gray-100 text-gray-800 border-gray-200'
  }

  const getCorrelationDirection = (correlation: number) => {
    if (correlation > 0.1) return 'Positive'
    if (correlation < -0.1) return 'Negative'
    return 'Neutral'
  }

  const getCorrelationIcon = (correlation: number) => {
    if (correlation > 0.1) return '↗️'
    if (correlation < -0.1) return '↘️'
    return '→'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Correlation Matrix</CardTitle>
        <p className="text-sm text-gray-600">
          Shows the strength and direction of relationships between metrics
        </p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="p-3 text-left font-semibold text-gray-700 bg-gray-50 border border-gray-200">
                  Metric
                </th>
                {metrics.map(metric => (
                  <th key={metric.key} className="p-3 text-center font-semibold text-gray-700 bg-gray-50 border border-gray-200">
                    {metric.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {metrics.map((metric, index) => (
                <tr key={metric.key} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="p-3 font-medium text-gray-900 border border-gray-200">
                    <div className="flex items-center space-x-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: metric.color }}
                      />
                      <span>{metric.name}</span>
                    </div>
                  </td>
                  {metrics.map((correlatedMetric) => {
                    const metricData = correlationMatrix[metric.key as keyof typeof correlationMatrix]
                    const correlation = metricData[correlatedMetric.key as keyof typeof metricData] as number
                    const isSelf = metric.key === correlatedMetric.key
                    
                    return (
                      <td key={correlatedMetric.key} className="p-3 text-center border border-gray-200">
                        {isSelf ? (
                          <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                            <span className="text-gray-500 text-sm">1.0</span>
                          </div>
                        ) : (
                          <div className="space-y-1">
                            <div className="text-lg font-bold text-gray-900">
                              {correlation.toFixed(2)}
                            </div>
                            <Badge className={`text-xs ${getCorrelationColor(correlation)}`}>
                              {getCorrelationStrength(correlation)}
                            </Badge>
                            <div className="text-xs text-gray-600">
                              {getCorrelationIcon(correlation)} {getCorrelationDirection(correlation)}
                            </div>
                          </div>
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="w-4 h-4 bg-green-100 border border-green-200 rounded mx-auto mb-1"></div>
            <span className="text-xs text-gray-600">Strong (0.7+)</span>
          </div>
          <div className="text-center">
            <div className="w-4 h-4 bg-yellow-100 border border-yellow-200 rounded mx-auto mb-1"></div>
            <span className="text-xs text-gray-600">Moderate (0.4-0.7)</span>
          </div>
          <div className="text-center">
            <div className="w-4 h-4 bg-blue-100 border border-blue-200 rounded mx-auto mb-1"></div>
            <span className="text-xs text-gray-600">Weak (0.2-0.4)</span>
          </div>
          <div className="text-center">
            <div className="w-4 h-4 bg-gray-100 border border-gray-200 rounded mx-auto mb-1"></div>
            <span className="text-xs text-gray-600">None (&lt;0.2)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
