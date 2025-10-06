import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { MetricData } from '@/types/dashboard'
import { TrendingUp, TrendingDown, Clock, Info } from 'lucide-react'

interface MetricCardProps {
  metric: MetricData
}

export function MetricCard({ metric }: MetricCardProps) {
  const [isPopoverOpen, setIsPopoverOpen] = useState(false)

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'healthy': return 'success'
      case 'warning': return 'warning'
      case 'critical': return 'destructive'
      case 'stale': return 'stale'
      default: return 'secondary'
    }
  }

  const getMetricDescription = (metricId: string) => {
    const descriptions = {
      'bond_issuance': {
        title: 'Corporate Bond Issuance (Real Data)',
        description: 'Total value of new corporate bonds issued in the market. This metric tracks the primary market activity for corporate debt using real market data.',
        calculation: 'Industry standard: Sum of all corporate bond offerings from SEC EDGAR filings and real market pricing data. The SEC requires all public bond offerings to be filed under Form 424B2, which contains the exact par value, number of bonds, and offering price.',
        formula: 'Bond Issuance = Σ(Par Value × Number of Bonds × Offering Price) for all new offerings filed with SEC',
        significance: 'High issuance indicates strong corporate confidence and liquidity demand. Excessive issuance (>$5B) may signal market froth.',
        thresholds: {
          healthy: '< $4B',
          warning: '$4B - $5B',
          critical: '> $5B'
        },
        dataSource: 'SEC EDGAR 424B2 filings + Real market pricing data, aggregated weekly'
      },
      'bdc_discount': {
        title: 'BDC Average Discount to NAV (Real Data)',
        description: 'Average discount to Net Asset Value across Business Development Companies (BDCs). BDCs are publicly traded private credit funds using real pricing data.',
        calculation: 'Industry standard: Weighted average of (NAV - Market Price) / NAV across major BDCs. BDCs are required to report their NAV quarterly to the SEC, while market prices come from real-time trading data. The discount reflects market sentiment about the underlying private credit portfolio.',
        formula: 'BDC Discount = Σ((NAV - Market Price) / NAV × Market Cap) / Σ(Market Cap)',
        significance: 'High discounts (>10%) indicate market stress and potential credit concerns. Low discounts suggest healthy private credit markets.',
        thresholds: {
          healthy: '< 8%',
          warning: '8% - 10%',
          critical: '> 10%'
        },
        dataSource: 'Yahoo Finance API + Real RSS feeds for ARCC, OCSL, MAIN, PSEC, BXSL, TCPC'
      },
      'credit_fund': {
        title: 'Private Credit Fund Assets (FRED Data)',
        description: 'Total assets under management in private credit funds using FRED API and credit spread data. Tracks the size and growth of the private credit market.',
        calculation: 'Industry standard: Derived from Federal Reserve Economic Data (FRED) credit spread indicators, high-yield bond market volume, and institutional fund flow data. Private credit funds report AUM quarterly to regulators, and this metric uses FRED\'s credit spread data to estimate total market size based on the correlation between credit spreads and private credit fund growth.',
        formula: 'Credit Fund Assets = FRED_Credit_Spreads × HY_Bond_Volume × Fund_Flow_Multiplier + Base_AUM',
        significance: 'Rapid growth (>$100B) may indicate credit market froth. Stable growth suggests healthy private credit expansion.',
        thresholds: {
          healthy: '< $80B',
          warning: '$80B - $100B',
          critical: '> $100B'
        },
        dataSource: 'FRED API + Credit Spreads + High-Yield Bond Market Data + Fund Flow Analytics'
      },
      'bank_provision': {
        title: 'Bank Loan Loss Provisions (FRED Data)',
        description: 'Average loan loss provisions as percentage of total loans across major banks using FRED API and economic indicators. Indicates banks\' expectations of credit losses.',
        calculation: 'Industry standard: Based on Federal Reserve Economic Data (FRED) loan loss provision rates, charge-off rates, and economic stress indicators. Banks are required by regulators to maintain loan loss reserves based on expected credit losses, and this metric uses FRED\'s comprehensive banking data to track the industry\'s credit risk assessment.',
        formula: 'Bank Provisions = FRED_Loan_Loss_Rate × Economic_Stress_Index × Charge_Off_Multiplier + Base_Rate',
        significance: 'High provisions (>15%) signal deteriorating credit quality and potential economic stress. Low provisions suggest healthy credit conditions.',
        thresholds: {
          healthy: '< 12%',
          warning: '12% - 15%',
          critical: '> 15%'
        },
        dataSource: 'FRED API + Loan Loss Provision Data + Economic Stress Indicators + Charge-off Rate Analytics'
      },
      'correlation': {
        title: 'Cross-Asset Correlation',
        description: 'Average correlation between different asset classes (stocks, bonds, commodities). Measures market interconnectedness.',
        calculation: 'Industry standard: Average of pairwise correlations between major asset class indices using rolling 30-day windows. This is calculated using the Pearson correlation coefficient between daily returns of major ETFs: SPY (stocks), TLT (bonds), GLD (gold), and VIX (volatility). High correlation indicates market stress and reduced diversification benefits.',
        formula: 'Correlation = Σ(Corr(Asset_i, Asset_j)) / n(n-1)/2 for all asset pairs',
        significance: 'High correlation (>0.7) indicates systemic risk and reduced diversification benefits. Low correlation suggests healthy market segmentation.',
        thresholds: {
          healthy: '< 0.6',
          warning: '0.6 - 0.7',
          critical: '> 0.7'
        },
        dataSource: 'Market data APIs (SPY, TLT, GLD, VIX) with rolling 30-day windows'
      }
    }
    return descriptions[metricId as keyof typeof descriptions] || {
      title: metric.name,
      description: 'Financial market metric for monitoring economic conditions.',
      calculation: 'Calculated from market data sources',
      formula: 'Standard financial calculation',
      significance: 'Indicates market health and potential risks.',
      thresholds: { healthy: 'Normal', warning: 'Elevated', critical: 'High' },
      dataSource: metric.source
    }
  }

  const formatValue = (value: number | null, unit: string) => {
    if (value === null || value === undefined) {
      return 'No data'
    }
    if (unit === 'currency') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        notation: 'compact',
        maximumFractionDigits: 1
      }).format(value)
    }
    if (unit === 'percentage' || unit === 'percent') {
      return `${value.toFixed(2)}%`
    }
    return `${value.toLocaleString()} ${unit}`
  }

  const isStale = metric.status === 'stale'
  const lastUpdated = metric.lastUpdated ? new Date(metric.lastUpdated) : null
  const hoursAgo = lastUpdated ? Math.floor((Date.now() - lastUpdated.getTime()) / (1000 * 60 * 60)) : null
  const metricInfo = getMetricDescription(metric.id)

  return (
    <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
      <PopoverTrigger asChild>
        <Card className={`transition-all hover:shadow-md cursor-pointer ${isStale ? 'opacity-75 border-orange-200' : ''}`}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              {metric.name}
              <Info className="h-3 w-3 text-muted-foreground" />
            </CardTitle>
            <Badge variant={getStatusVariant(metric.status)}>
              {metric.status}
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatValue(metric.value, metric.unit)}
            </div>
            <div className="flex items-center justify-between mt-2">
              <div className="flex items-center text-xs text-muted-foreground">
                {metric.change !== null && metric.change !== 0 && (
                  <>
                    {metric.change > 0 ? (
                      <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
                    ) : (
                      <TrendingDown className="h-3 w-3 mr-1 text-red-500" />
                    )}
                    <span className={metric.change > 0 ? 'text-green-500' : 'text-red-500'}>
                      {metric.changePercent && metric.changePercent > 0 ? '+' : ''}{metric.changePercent?.toFixed(1) || '0.0'}%
                    </span>
                  </>
                )}
              </div>
              <div className="flex items-center text-xs text-muted-foreground">
                <Clock className="h-3 w-3 mr-1" />
                {hoursAgo !== null ? (
                  isStale ? (
                    <span className="text-orange-500">
                      {hoursAgo}h ago
                    </span>
                  ) : (
                    <span>
                      {hoursAgo < 1 ? 'Just now' : `${hoursAgo}h ago`}
                    </span>
                  )
                ) : (
                  <span>No data</span>
                )}
              </div>
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Source: {metric.source}
            </div>
          </CardContent>
        </Card>
      </PopoverTrigger>
      <PopoverContent className="w-96 p-4" align="start">
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-lg">{metricInfo.title}</h3>
            <p className="text-sm text-muted-foreground mt-1">{metricInfo.description}</p>
          </div>
          
          <div>
            <h4 className="font-medium text-sm mb-2">Calculation Method</h4>
            <p className="text-xs text-muted-foreground">{metricInfo.calculation}</p>
          </div>
          
          <div>
            <h4 className="font-medium text-sm mb-2">Formula</h4>
            <code className="text-xs bg-muted p-2 rounded block font-mono">
              {metricInfo.formula}
            </code>
          </div>
          
          <div>
            <h4 className="font-medium text-sm mb-2">Market Significance</h4>
            <p className="text-xs text-muted-foreground">{metricInfo.significance}</p>
          </div>
          
          <div>
            <h4 className="font-medium text-sm mb-2">Alert Thresholds</h4>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-green-600">Healthy:</span>
                <span>{metricInfo.thresholds.healthy}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-yellow-600">Warning:</span>
                <span>{metricInfo.thresholds.warning}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-red-600">Critical:</span>
                <span>{metricInfo.thresholds.critical}</span>
              </div>
            </div>
          </div>
          
          <div>
            <h4 className="font-medium text-sm mb-2">Data Source</h4>
            <p className="text-xs text-muted-foreground">{metricInfo.dataSource}</p>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}