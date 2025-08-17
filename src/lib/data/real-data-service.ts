import fs from 'fs'
import path from 'path'

interface ScraperDataPoint {
  data_source: string
  metric_name: string
  timestamp: string
  data: {
    value: number
    timestamp: string
    confidence: number
    metadata?: any
    validation_checksum?: string
    anomaly_score?: number
  }
}

interface RealDataService {
  getLatestMetrics(): Promise<any[]>
  getHistoricalData(metricKey: string, days: number): Promise<any[]>
  getDataSources(): Promise<string[]>
}

class FileBasedRealDataService implements RealDataService {
  private dataDir = '/Users/turphai/Projects/kiro_aiCrash/data'

  async getLatestMetrics(): Promise<any[]> {
    try {
      const files = await this.getDataFiles()
      const metrics: any[] = []

      for (const file of files) {
        const data = await this.readDataFile(file)
        
        if (data.length > 0) {
          const latest = data[0] // Most recent data point
          const metricKey = this.getMetricKey(latest.data_source, latest.metric_name)
          
          // Calculate change from previous data point if available
          let change = 0
          let changePercent = 0
          if (data.length > 1) {
            const previous = data[1]
            change = latest.data.value - previous.data.value
            changePercent = previous.data.value !== 0 
              ? (change / previous.data.value) * 100 
              : 0
          }

          // Determine status based on thresholds
          const status = this.getStatus(latest.data.value, metricKey)

          const metric = {
            key: metricKey,
            name: this.formatMetricName(latest.data_source, latest.metric_name),
            value: latest.data.value,
            unit: this.getUnit(metricKey),
            change,
            changePercent,
            status,
            lastUpdated: latest.timestamp,
            source: latest.data_source,
            confidence: latest.data.confidence,
            metadata: latest.data.metadata
          }
          
          metrics.push(metric)
        }
      }

      return metrics
    } catch (error) {
      console.error('Error reading real data:', error)
      return []
    }
  }

  async getHistoricalData(metricKey: string, days: number): Promise<any[]> {
    try {
      const files = await this.getDataFiles()
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - days)

      for (const file of files) {
        const data = await this.readDataFile(file)
        if (data.length > 0) {
          const fileMetricKey = this.getMetricKey(data[0].data_source, data[0].metric_name)
          
          if (fileMetricKey === metricKey) {
            return data
              .filter(point => new Date(point.timestamp) >= cutoffDate)
              .map(point => ({
                timestamp: point.timestamp,
                value: point.data.value,
                metadata: point.data.metadata
              }))
              .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
          }
        }
      }

      return []
    } catch (error) {
      console.error('Error reading historical data:', error)
      return []
    }
  }

  async getDataSources(): Promise<string[]> {
    try {
      const files = await this.getDataFiles()
      const sources = new Set<string>()

      for (const file of files) {
        const data = await this.readDataFile(file)
        if (data.length > 0) {
          sources.add(data[0].data_source)
        }
      }

      return Array.from(sources)
    } catch (error) {
      console.error('Error reading data sources:', error)
      return []
    }
  }

  private async getDataFiles(): Promise<string[]> {
    try {
      const files = await fs.promises.readdir(this.dataDir)
      return files
        .filter(file => file.endsWith('.json'))
        .filter(file => !file.includes('dashboard_alerts')) // Skip alert history files
        .filter(file => !file.includes('test_')) // Skip test files
        .filter(file => !file.includes('health_check_')) // Skip health check test files
        .filter(file => !file.includes('comprehensive_test_')) // Skip comprehensive test files
        .map(file => path.join(this.dataDir, file))
    } catch (error) {
      console.error('Error reading data directory:', error)
      return []
    }
  }

  private async readDataFile(filePath: string): Promise<ScraperDataPoint[]> {
    try {
      const content = await fs.promises.readFile(filePath, 'utf-8')
      return JSON.parse(content)
    } catch (error) {
      console.error(`Error reading file ${filePath}:`, error)
      return []
    }
  }

  private getMetricKey(dataSource: string, metricName: string): string {
    // Map scraper data sources to dashboard metric keys
    const mapping: Record<string, string> = {
      'bond_issuance': 'bond_issuance',
      'bdc_discount': 'bdc_discount',
      'credit_fund': 'credit_fund',
      'bank_provision': 'bank_provision'
    }

    // Handle specific metric name mappings for legitimate scrapers
    if (dataSource === 'bond_issuance' && metricName === 'weekly') {
      return 'bond_issuance'
    }
    if (dataSource === 'bdc_discount' && metricName === 'discount_to_nav') {
      return 'bdc_discount'
    }

    return mapping[dataSource] || `${dataSource}_${metricName}`
  }

  private formatMetricName(dataSource: string, metricName: string): string {
    const nameMapping: Record<string, string> = {
      'bond_issuance': 'Bond Issuance',
      'bdc_discount': 'BDC Discount',
      'credit_fund': 'Credit Fund Assets',
      'bank_provision': 'Bank Provisions'
    }

    return nameMapping[dataSource] || `${dataSource} ${metricName}`.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  private getUnit(metricKey: string): string {
    const unitMapping: Record<string, string> = {
      'bond_issuance': 'currency',
      'bdc_discount': 'percent',
      'credit_fund': 'currency',
      'bank_provision': 'percent'
    }

    return unitMapping[metricKey] || 'unit'
  }

  private getStatus(value: number, metricKey: string): 'healthy' | 'warning' | 'critical' | 'stale' {
    const thresholds: Record<string, { warning: number; critical: number }> = {
      'bond_issuance': { warning: 4000000000, critical: 5000000000 }, // $4B, $5B
      'bdc_discount': { warning: 8, critical: 10 }, // 8%, 10%
      'credit_fund': { warning: 80000000000, critical: 100000000000 }, // $80B, $100B
      'bank_provision': { warning: 12, critical: 15 } // 12%, 15%
    }

    const threshold = thresholds[metricKey]
    if (!threshold) return 'healthy'

    if (value >= threshold.critical) return 'critical'
    if (value >= threshold.warning) return 'warning'
    return 'healthy'
  }
}

// Export singleton instance
export const realDataService = new FileBasedRealDataService()
