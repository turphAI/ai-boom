import { MetricData, HistoricalData } from '@/types/dashboard'

export interface MockAnalyticsData {
  bondIssuance: BondIssuanceAnalytics
  bdcDiscount: BdcDiscountAnalytics
  creditFunds: CreditFundAnalytics
  bankProvisions: BankProvisionsAnalytics
  correlations: CrossMetricAnalytics
}

export interface BondIssuanceAnalytics {
  summary: {
    totalIssuance: number
    trend: 'increasing' | 'decreasing' | 'stable'
    changePercent: number
    redFlags: string[]
  }
  byCategory: {
    demand: { issuance: number; entities: string[]; trend: string; changePercent: number }
    supply: { issuance: number; entities: string[]; trend: string; changePercent: number }
    financing: { issuance: number; entities: string[]; trend: string; changePercent: number }
  }
  correlations: {
    withBdcDiscount: number
    withCreditFunds: number
    withBankProvisions: number
  }
}

export interface BdcDiscountAnalytics {
  summary: {
    averageDiscount: number
    trend: 'increasing' | 'decreasing' | 'stable'
    changePercent: number
    redFlags: string[]
  }
  byCategory: {
    technology: { avgDiscount: number; entities: string[]; trend: string; changePercent: number }
    infrastructure: { avgDiscount: number; entities: string[]; trend: string; changePercent: number }
    generalist: { avgDiscount: number; entities: string[]; trend: string; changePercent: number }
  }
  correlations: {
    withBondIssuance: number
    withCreditFunds: number
    withBankProvisions: number
  }
}

export interface CreditFundAnalytics {
  summary: {
    totalFlows: number
    trend: 'increasing' | 'decreasing' | 'stable'
    changePercent: number
    redFlags: string[]
  }
  byCategory: {
    privateCredit: { flows: number; entities: string[]; trend: string; changePercent: number }
    ventureDebt: { flows: number; entities: string[]; trend: string; changePercent: number }
    infrastructure: { flows: number; entities: string[]; trend: string; changePercent: number }
  }
  correlations: {
    withBondIssuance: number
    withBdcDiscount: number
    withBankProvisions: number
  }
}

export interface BankProvisionsAnalytics {
  summary: {
    totalProvisions: number
    trend: 'increasing' | 'decreasing' | 'stable'
    changePercent: number
    redFlags: string[]
  }
  byCategory: {
    largeBanks: { provisions: number; entities: string[]; trend: string; changePercent: number }
    regionalBanks: { provisions: number; entities: string[]; trend: string; changePercent: number }
    techFocused: { provisions: number; entities: string[]; trend: string; changePercent: number }
  }
  correlations: {
    withBondIssuance: number
    withBdcDiscount: number
    withCreditFunds: number
  }
}

export interface CrossMetricAnalytics {
  correlationMatrix: {
    bondIssuance: { bdcDiscount: number; creditFunds: number; bankProvisions: number }
    bdcDiscount: { bondIssuance: number; creditFunds: number; bankProvisions: number }
    creditFunds: { bondIssuance: number; bdcDiscount: number; bankProvisions: number }
    bankProvisions: { bondIssuance: number; bdcDiscount: number; creditFunds: number }
  }
  cyclePhase: {
    phase: 'expansion' | 'peak' | 'contraction' | 'trough'
    confidence: number
    indicators: string[]
    description: string
    nextPhase: string
    timeframe: string
  }
  keyInsights: string[]
  riskFactors: string[]
  opportunities: string[]
  leadingIndicators: {
    name: string
    value: number
    trend: string
    impact: 'positive' | 'negative' | 'neutral'
  }[]
}

class MockAnalyticsService {
  private baseMetrics: MetricData[] = []
  private historicalData: HistoricalData[] = []

  constructor() {
    this.generateBaseMetrics()
    this.generateHistoricalData()
  }

  private generateBaseMetrics() {
    // Generate realistic base metrics with correlations
    const baseValues = {
      bond_issuance: 8500000000, // $8.5B
      bdc_discount: 12.5, // 12.5%
      credit_fund: 15000000000, // $15B
      bank_provision: 8500000000 // $8.5B
    }

    const changes = {
      bond_issuance: 28.5,
      bdc_discount: 15.8,
      credit_fund: -12.3,
      bank_provision: 22.1
    }

    this.baseMetrics = Object.entries(baseValues).map(([key, value]) => ({
      id: key,
      key,
      name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value,
      unit: key === 'bdc_discount' ? '%' : '$',
      change: value * (changes[key as keyof typeof changes] / 100),
      changePercent: changes[key as keyof typeof changes],
      status: this.calculateStatus(key, value, changes[key as keyof typeof changes]),
      lastUpdated: new Date().toISOString(),
      source: 'mock_data',
      confidence: 0.85,
      metadata: {}
    }))
  }

  private calculateStatus(key: string, value: number, changePercent: number): 'healthy' | 'warning' | 'critical' {
    const thresholds = {
      bond_issuance: { warning: 5000000000, critical: 10000000000 },
      bdc_discount: { warning: 10, critical: 20 },
      credit_fund: { warning: 10000000000, critical: 5000000000 },
      bank_provision: { warning: 5000000000, critical: 10000000000 }
    }

    const threshold = thresholds[key as keyof typeof thresholds]
    if (!threshold) return 'healthy'

    if (key === 'bdc_discount' || key === 'bank_provision') {
      // Higher values are worse for these metrics
      if (value >= threshold.critical) return 'critical'
      if (value >= threshold.warning) return 'warning'
    } else {
      // Lower values are worse for these metrics
      if (value <= threshold.critical) return 'critical'
      if (value <= threshold.warning) return 'warning'
    }

    return 'healthy'
  }

  private generateHistoricalData() {
    const now = new Date()
    const data: HistoricalData[] = []

    // Generate 365 days of historical data
    for (let i = 365; i >= 0; i--) {
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
      
      // Add some realistic volatility and trends
      const volatility = 0.1
      const trend = Math.sin(i / 30) * 0.2 // Seasonal pattern
      
      this.baseMetrics.forEach(metric => {
        const baseValue = metric.value
        const randomFactor = 1 + (Math.random() - 0.5) * volatility
        const trendFactor = 1 + trend
        const value = baseValue * randomFactor * trendFactor

        data.push({
          timestamp: date.toISOString(),
          value: Math.max(0, value),
          metadata: { volatility, trend, metricKey: metric.id }
        })
      })
    }

    this.historicalData = data
  }

  public getBondIssuanceAnalytics(): BondIssuanceAnalytics {
    const metric = this.baseMetrics.find(m => m.id === 'bond_issuance')!
    
    return {
      summary: {
        totalIssuance: metric.value,
        trend: metric.changePercent > 10 ? 'increasing' : metric.changePercent < -10 ? 'decreasing' : 'stable',
        changePercent: metric.changePercent,
        redFlags: this.generateRedFlags('bond_issuance', metric)
      },
      byCategory: {
        demand: {
          issuance: metric.value * 0.4,
          entities: ['Amazon', 'Google', 'Meta', 'Microsoft', 'NVIDIA'],
          trend: 'increasing',
          changePercent: 35.2
        },
        supply: {
          issuance: metric.value * 0.35,
          entities: ['Equinix', 'Digital Realty', 'CyrusOne', 'CoreWeave'],
          trend: 'stable',
          changePercent: 8.5
        },
        financing: {
          issuance: metric.value * 0.25,
          entities: ['Ares Capital', 'Main Street Capital', 'Hercules Capital'],
          trend: 'decreasing',
          changePercent: -12.8
        }
      },
      correlations: {
        withBdcDiscount: 0.72,
        withCreditFunds: -0.45,
        withBankProvisions: 0.38
      }
    }
  }

  public getBdcDiscountAnalytics(): BdcDiscountAnalytics {
    const metric = this.baseMetrics.find(m => m.id === 'bdc_discount')!
    
    return {
      summary: {
        averageDiscount: metric.value,
        trend: metric.changePercent > 5 ? 'increasing' : metric.changePercent < -5 ? 'decreasing' : 'stable',
        changePercent: metric.changePercent,
        redFlags: this.generateRedFlags('bdc_discount', metric)
      },
      byCategory: {
        technology: {
          avgDiscount: metric.value * 1.2,
          entities: ['Hercules Capital', 'Trinity Capital', 'Horizon Technology'],
          trend: 'increasing',
          changePercent: 15.8
        },
        infrastructure: {
          avgDiscount: metric.value * 0.9,
          entities: ['Main Street Capital', 'Blue Owl Capital', 'OFS Capital'],
          trend: 'stable',
          changePercent: 2.3
        },
        generalist: {
          avgDiscount: metric.value * 1.1,
          entities: ['Ares Capital', 'TP Venture Growth', 'Prospect Capital'],
          trend: 'decreasing',
          changePercent: -8.5
        }
      },
      correlations: {
        withBondIssuance: 0.72,
        withCreditFunds: -0.38,
        withBankProvisions: 0.45
      }
    }
  }

  public getCreditFundAnalytics(): CreditFundAnalytics {
    const metric = this.baseMetrics.find(m => m.id === 'credit_fund')!
    
    return {
      summary: {
        totalFlows: metric.value,
        trend: metric.changePercent > 10 ? 'increasing' : metric.changePercent < -10 ? 'decreasing' : 'stable',
        changePercent: metric.changePercent,
        redFlags: this.generateRedFlags('credit_fund', metric)
      },
      byCategory: {
        privateCredit: {
          flows: metric.value * 0.5,
          entities: ['Blackstone Group', 'KKR & Co', 'Apollo Global Management'],
          trend: 'decreasing',
          changePercent: -18.5
        },
        ventureDebt: {
          flows: metric.value * 0.3,
          entities: ['Hercules Capital', 'Trinity Capital', 'Horizon Technology'],
          trend: 'stable',
          changePercent: 3.2
        },
        infrastructure: {
          flows: metric.value * 0.2,
          entities: ['Brookfield Asset Management', 'DigitalBridge Group', 'American Tower'],
          trend: 'increasing',
          changePercent: 25.8
        }
      },
      correlations: {
        withBondIssuance: -0.45,
        withBdcDiscount: -0.38,
        withBankProvisions: 0.52
      }
    }
  }

  public getBankProvisionsAnalytics(): BankProvisionsAnalytics {
    const metric = this.baseMetrics.find(m => m.id === 'bank_provision')!
    
    return {
      summary: {
        totalProvisions: metric.value,
        trend: metric.changePercent > 15 ? 'increasing' : metric.changePercent < -15 ? 'decreasing' : 'stable',
        changePercent: metric.changePercent,
        redFlags: this.generateRedFlags('bank_provision', metric)
      },
      byCategory: {
        largeBanks: {
          provisions: metric.value * 0.6,
          entities: ['JPMorgan Chase', 'Bank of America', 'Wells Fargo', 'Citigroup'],
          trend: 'increasing',
          changePercent: 28.5
        },
        regionalBanks: {
          provisions: metric.value * 0.25,
          entities: ['PNC Financial', 'US Bancorp', 'Truist Financial', 'KeyCorp'],
          trend: 'stable',
          changePercent: 5.2
        },
        techFocused: {
          provisions: metric.value * 0.15,
          entities: ['Silicon Valley Bank', 'First Republic', 'Signature Bank'],
          trend: 'increasing',
          changePercent: 45.8
        }
      },
      correlations: {
        withBondIssuance: 0.38,
        withBdcDiscount: 0.45,
        withCreditFunds: 0.52
      }
    }
  }

  public getCrossMetricAnalytics(): CrossMetricAnalytics {
    const bondIssuance = this.getBondIssuanceAnalytics()
    const bdcDiscount = this.getBdcDiscountAnalytics()
    const creditFunds = this.getCreditFundAnalytics()
    const bankProvisions = this.getBankProvisionsAnalytics()

    // Determine cycle phase based on metrics
    const cyclePhase = this.determineCyclePhase()

    return {
      correlationMatrix: {
        bondIssuance: {
          bdcDiscount: bondIssuance.correlations.withBdcDiscount,
          creditFunds: bondIssuance.correlations.withCreditFunds,
          bankProvisions: bondIssuance.correlations.withBankProvisions
        },
        bdcDiscount: {
          bondIssuance: bdcDiscount.correlations.withBondIssuance,
          creditFunds: bdcDiscount.correlations.withCreditFunds,
          bankProvisions: bdcDiscount.correlations.withBankProvisions
        },
        creditFunds: {
          bondIssuance: creditFunds.correlations.withBondIssuance,
          bdcDiscount: creditFunds.correlations.withBdcDiscount,
          bankProvisions: creditFunds.correlations.withBankProvisions
        },
        bankProvisions: {
          bondIssuance: bankProvisions.correlations.withBondIssuance,
          bdcDiscount: bankProvisions.correlations.withBdcDiscount,
          creditFunds: bankProvisions.correlations.withCreditFunds
        }
      },
      cyclePhase,
      keyInsights: this.generateKeyInsights(),
      riskFactors: this.generateRiskFactors(),
      opportunities: this.generateOpportunities(),
      leadingIndicators: this.generateLeadingIndicators()
    }
  }

  private determineCyclePhase(): CrossMetricAnalytics['cyclePhase'] {
    const bondIssuance = this.baseMetrics.find(m => m.id === 'bond_issuance')!
    const bdcDiscount = this.baseMetrics.find(m => m.id === 'bdc_discount')!
    const creditFunds = this.baseMetrics.find(m => m.id === 'credit_fund')!
    const bankProvisions = this.baseMetrics.find(m => m.id === 'bank_provision')!

    // Simple logic to determine cycle phase
    if (bondIssuance.changePercent > 20 && bdcDiscount.changePercent < 10 && creditFunds.changePercent > 0) {
      return {
        phase: 'expansion',
        confidence: 0.78,
        indicators: [
          'High bond issuance driving infrastructure investment',
          'BDC discounts within normal range',
          'Credit funds flowing into sector',
          'Bank provisions stable'
        ],
        description: 'The AI datacenter sector is in expansion phase with strong capital flows and moderate risk indicators.',
        nextPhase: 'peak',
        timeframe: '6-12 months'
      }
    } else if (bondIssuance.changePercent > 30 && bdcDiscount.changePercent > 20) {
      return {
        phase: 'peak',
        confidence: 0.85,
        indicators: [
          'Excessive debt issuance',
          'BDC stress widening',
          'Credit flows slowing',
          'Bank provisions rising'
        ],
        description: 'The sector is showing signs of overheating with high debt levels and increasing stress indicators.',
        nextPhase: 'contraction',
        timeframe: '3-6 months'
      }
    } else if (bondIssuance.changePercent < -10 && creditFunds.changePercent < -20) {
      return {
        phase: 'contraction',
        confidence: 0.72,
        indicators: [
          'Debt issuance declining',
          'Credit flows drying up',
          'BDC stress elevated',
          'Bank provisions high'
        ],
        description: 'The sector is contracting with reduced capital flows and elevated risk indicators.',
        nextPhase: 'trough',
        timeframe: '6-12 months'
      }
    } else {
      return {
        phase: 'trough',
        confidence: 0.65,
        indicators: [
          'Low debt issuance',
          'Credit flows minimal',
          'BDC stress high',
          'Bank provisions elevated'
        ],
        description: 'The sector is in a trough with minimal investment activity and high risk indicators.',
        nextPhase: 'expansion',
        timeframe: '12-18 months'
      }
    }
  }

  private generateRedFlags(metricKey: string, metric: MetricData): string[] {
    const flags: string[] = []

    switch (metricKey) {
      case 'bond_issuance':
        if (metric.changePercent > 50) flags.push('High debt issuance spike')
        if (metric.value > 5000000000) flags.push('Excessive debt levels')
        break
      case 'bdc_discount':
        if (metric.changePercent > 20) flags.push('BDC stress widening rapidly')
        if (metric.value > 15) flags.push('High discount levels indicating market stress')
        break
      case 'credit_fund':
        if (metric.changePercent < -20) flags.push('Credit flow slowdown detected')
        if (metric.value < 10000000000) flags.push('Low fund activity levels')
        break
      case 'bank_provision':
        if (metric.changePercent > 30) flags.push('Bank risk rising rapidly')
        if (metric.value > 10000000000) flags.push('High provision levels indicating systemic risk')
        break
    }

    return flags
  }

  private generateKeyInsights(): string[] {
    return [
      'Bond issuance strongly correlates with BDC stress (0.72)',
      'Credit fund flows inversely related to debt issuance (-0.45)',
      'Bank provisions rising but still manageable',
      'Technology BDCs showing early stress signals'
    ]
  }

  private generateRiskFactors(): string[] {
    return [
      'Rapid debt accumulation could lead to BDC stress',
      'Credit fund slowdown may signal capital constraints',
      'Bank provisions trending upward',
      'Regional bank exposure to tech sector'
    ]
  }

  private generateOpportunities(): string[] {
    return [
      'Infrastructure investment opportunities in expansion phase',
      'Private credit alternatives to traditional debt',
      'Regional bank partnerships for smaller projects',
      'Technology-focused BDC investments'
    ]
  }

  private generateLeadingIndicators(): CrossMetricAnalytics['leadingIndicators'] {
    return [
      {
        name: 'Bond Issuance Momentum',
        value: 0.85,
        trend: 'increasing',
        impact: 'negative'
      },
      {
        name: 'BDC Stress Index',
        value: 0.42,
        trend: 'stable',
        impact: 'neutral'
      },
      {
        name: 'Credit Flow Velocity',
        value: 0.68,
        trend: 'decreasing',
        impact: 'negative'
      },
      {
        name: 'Bank Risk Appetite',
        value: 0.31,
        trend: 'decreasing',
        impact: 'negative'
      }
    ]
  }

  public getHistoricalData(metricKey?: string): HistoricalData[] {
    if (metricKey) {
      return this.historicalData.filter(d => d.metadata?.metricKey === metricKey)
    }
    return this.historicalData
  }

  public getCurrentMetrics(): MetricData[] {
    return this.baseMetrics
  }

  public refreshData() {
    this.generateBaseMetrics()
    this.generateHistoricalData()
  }

  // Advanced visualization data generators
  generateHeatmapData(): any[] {
    const metrics = ['bond_issuance', 'bdc_discount', 'credit_fund', 'bank_provision']
    const data = []
    
    for (let i = 0; i < metrics.length; i++) {
      for (let j = 0; j < metrics.length; j++) {
        if (i !== j) {
          const correlation = Math.random() * 2 - 1 // -1 to 1
          data.push({
            x: metrics[i],
            y: metrics[j],
            value: Math.abs(correlation),
            correlation: correlation
          })
        }
      }
    }
    
    return data
  }

  generateScatterData(): any[] {
    const data = []
    const baseValue = 1000
    
    for (let i = 0; i < 50; i++) {
      const x = Math.random() * 1000 + 500
      const y = x * (0.8 + Math.random() * 0.4) + (Math.random() - 0.5) * 200
      data.push({
        x: x,
        y: y,
        label: `Point ${i + 1}`,
        category: i % 3 === 0 ? 'High' : i % 3 === 1 ? 'Medium' : 'Low'
      })
    }
    
    return data
  }

  generateBubbleData(): any[] {
    const data = []
    const categories = ['Technology', 'Healthcare', 'Energy', 'Finance']
    
    for (let i = 0; i < 30; i++) {
      data.push({
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: Math.random() * 50 + 10,
        label: `Company ${i + 1}`,
        category: categories[i % categories.length],
        color: undefined // Will be auto-assigned
      })
    }
    
    return data
  }

  generatePredictiveData(): any[] {
    const data = []
    const baseValue = 1000
    let currentValue = baseValue
    
    for (let i = 0; i < 24; i++) {
      const trend = Math.sin(i * 0.3) * 50 + Math.random() * 20
      currentValue += trend
      
      data.push({
        timestamp: new Date(Date.now() - (24 - i) * 24 * 60 * 60 * 1000).toISOString(),
        value: Math.max(0, currentValue),
        trend: trend > 0 ? 'up' : trend < 0 ? 'down' : 'stable'
      })
    }
    
    return data
  }
}

// Export singleton instance
// export const mockAnalyticsService = new MockAnalyticsService()
