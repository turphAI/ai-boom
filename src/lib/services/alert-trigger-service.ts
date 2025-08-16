import { realDataService } from '@/lib/data/real-data-service'

interface AlertThreshold {
  id: string
  metricKey: string
  thresholdType: 'absolute' | 'percentage' | 'standard_deviation'
  thresholdValue: number
  comparisonOperator: 'gt' | 'lt' | 'gte' | 'lte' | 'eq'
  severity: 'low' | 'medium' | 'high' | 'critical'
  enabled: boolean
  description: string
}

interface AlertTrigger {
  id: string
  thresholdId: string
  metricKey: string
  currentValue: number
  thresholdValue: number
  severity: string
  message: string
  timestamp: string
  triggered: boolean
}

interface MetricData {
  id: string
  name: string
  value: number
  unit: string
  change: number
  changePercent: number
  status: string
  lastUpdated: string
  source: string
  confidence: number
  metadata?: any
}

class AlertTriggerService {
  private thresholds: AlertThreshold[] = [
    // Bond Issuance thresholds
    {
      id: 'bond_issuance_warning',
      metricKey: 'bond_issuance',
      thresholdType: 'absolute',
      thresholdValue: 4000000000, // $4B
      comparisonOperator: 'gte',
      severity: 'medium',
      enabled: true,
      description: 'Bond issuance exceeds $4B warning threshold'
    },
    {
      id: 'bond_issuance_critical',
      metricKey: 'bond_issuance',
      thresholdType: 'absolute',
      thresholdValue: 5000000000, // $5B
      comparisonOperator: 'gte',
      severity: 'critical',
      enabled: true,
      description: 'Bond issuance exceeds $5B critical threshold'
    },
    
    // BDC Discount thresholds
    {
      id: 'bdc_discount_warning',
      metricKey: 'bdc_discount',
      thresholdType: 'absolute',
      thresholdValue: 8, // 8%
      comparisonOperator: 'gte',
      severity: 'medium',
      enabled: true,
      description: 'BDC discount exceeds 8% warning threshold'
    },
    {
      id: 'bdc_discount_critical',
      metricKey: 'bdc_discount',
      thresholdType: 'absolute',
      thresholdValue: 10, // 10%
      comparisonOperator: 'gte',
      severity: 'critical',
      enabled: true,
      description: 'BDC discount exceeds 10% critical threshold'
    },
    
    // Credit Fund thresholds
    {
      id: 'credit_fund_warning',
      metricKey: 'credit_fund',
      thresholdType: 'absolute',
      thresholdValue: 80000000000, // $80B
      comparisonOperator: 'gte',
      severity: 'medium',
      enabled: true,
      description: 'Credit fund assets exceed $80B warning threshold'
    },
    {
      id: 'credit_fund_critical',
      metricKey: 'credit_fund',
      thresholdType: 'absolute',
      thresholdValue: 100000000000, // $100B
      comparisonOperator: 'gte',
      severity: 'critical',
      enabled: true,
      description: 'Credit fund assets exceed $100B critical threshold'
    },
    
    // Bank Provision thresholds
    {
      id: 'bank_provision_warning',
      metricKey: 'bank_provision',
      thresholdType: 'absolute',
      thresholdValue: 12, // 12%
      comparisonOperator: 'gte',
      severity: 'medium',
      enabled: true,
      description: 'Bank provisions exceed 12% warning threshold'
    },
    {
      id: 'bank_provision_critical',
      metricKey: 'bank_provision',
      thresholdType: 'absolute',
      thresholdValue: 15, // 15%
      comparisonOperator: 'gte',
      severity: 'critical',
      enabled: true,
      description: 'Bank provisions exceed 15% critical threshold'
    }
  ]

  async evaluateAlerts(): Promise<AlertTrigger[]> {
    try {
      const metrics = await realDataService.getLatestMetrics()
      const triggers: AlertTrigger[] = []

      for (const metric of metrics) {
        const metricThresholds = this.thresholds.filter(t => 
          t.metricKey === metric.id && t.enabled
        )

        for (const threshold of metricThresholds) {
          const triggered = this.evaluateThreshold(metric, threshold)
          
          if (triggered) {
            const trigger: AlertTrigger = {
              id: `${threshold.id}_${Date.now()}`,
              thresholdId: threshold.id,
              metricKey: metric.id,
              currentValue: metric.value,
              thresholdValue: threshold.thresholdValue,
              severity: threshold.severity,
              message: this.generateAlertMessage(metric, threshold),
              timestamp: new Date().toISOString(),
              triggered: true
            }
            
            triggers.push(trigger)
          }
        }
      }

      return triggers
    } catch (error) {
      console.error('Error evaluating alerts:', error)
      return []
    }
  }

  private evaluateThreshold(metric: MetricData, threshold: AlertThreshold): boolean {
    const { value } = metric
    const { thresholdValue, comparisonOperator } = threshold

    switch (comparisonOperator) {
      case 'gt':
        return value > thresholdValue
      case 'lt':
        return value < thresholdValue
      case 'gte':
        return value >= thresholdValue
      case 'lte':
        return value <= thresholdValue
      case 'eq':
        return value === thresholdValue
      default:
        return false
    }
  }

  private generateAlertMessage(metric: MetricData, threshold: AlertThreshold): string {
    const { name, value, unit, changePercent } = metric
    const { thresholdValue, severity, description } = threshold
    
    const formatValue = (val: number, unit: string) => {
      if (unit === 'currency') {
        return `$${(val / 1000000000).toFixed(1)}B`
      } else if (unit === 'percent') {
        return `${(val * 100).toFixed(1)}%`
      }
      return val.toLocaleString()
    }

    const currentFormatted = formatValue(value, unit)
    const thresholdFormatted = formatValue(thresholdValue, unit)
    const changeText = changePercent !== 0 ? ` (${changePercent > 0 ? '+' : ''}${changePercent.toFixed(1)}% from previous)` : ''

    return `🚨 ${severity.toUpperCase()} ALERT: ${name}${changeText}

Current: ${currentFormatted}
Threshold: ${thresholdFormatted}
Status: ${description}

Time: ${new Date().toLocaleString()}`
  }

  async getThresholds(): Promise<AlertThreshold[]> {
    return this.thresholds
  }

  async updateThreshold(threshold: AlertThreshold): Promise<void> {
    const index = this.thresholds.findIndex(t => t.id === threshold.id)
    if (index !== -1) {
      this.thresholds[index] = threshold
    } else {
      this.thresholds.push(threshold)
    }
  }

  async deleteThreshold(thresholdId: string): Promise<void> {
    this.thresholds = this.thresholds.filter(t => t.id !== thresholdId)
  }
}

export const alertTriggerService = new AlertTriggerService()
