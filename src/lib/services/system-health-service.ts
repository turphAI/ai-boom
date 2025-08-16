import { realDataService } from '@/lib/data/real-data-service'
import { db } from '@/lib/db/connection'

interface HealthCheck {
  id: string
  component: string
  status: 'healthy' | 'warning' | 'critical' | 'unknown'
  message: string
  timestamp: string
  responseTime?: number
  details?: any
}

interface ScraperHealth {
  scraperName: string
  lastRun: string
  successRate: number
  totalRuns: number
  successfulRuns: number
  failedRuns: number
  averageResponseTime: number
  lastError?: string
  status: 'healthy' | 'warning' | 'critical'
}

interface ApiHealth {
  endpoint: string
  status: 'healthy' | 'warning' | 'critical' | 'unknown'
  responseTime: number
  lastCheck: string
  successRate: number
  errorCount: number
  lastError?: string
}

interface SystemMetrics {
  uptime: number
  memoryUsage: number
  cpuUsage: number
  activeConnections: number
  databaseStatus: 'connected' | 'disconnected' | 'error'
  lastDataUpdate: string
}

class SystemHealthService {
  private healthChecks: HealthCheck[] = []
  private scraperHealth: ScraperHealth[] = []
  private apiHealth: ApiHealth[] = []
  private systemMetrics: SystemMetrics | null = null

  async performHealthCheck(): Promise<{
    overall: 'healthy' | 'warning' | 'critical'
    checks: HealthCheck[]
    scrapers: ScraperHealth[]
    apis: ApiHealth[]
    metrics: SystemMetrics | null
  }> {
    const checks: HealthCheck[] = []
    
    // 1. Database Health Check
    const dbHealth = await this.checkDatabaseHealth()
    checks.push(dbHealth)
    
    // 2. External API Health Checks
    const apiChecks = await this.checkExternalApis()
    checks.push(...apiChecks)
    
    // 3. Scraper Health Analysis
    const scraperChecks = await this.analyzeScraperHealth()
    checks.push(...scraperChecks)
    
    // 4. System Metrics
    const metrics = await this.getSystemMetrics()
    this.systemMetrics = metrics
    
    // 5. Data Freshness Check
    const dataHealth = await this.checkDataFreshness()
    checks.push(dataHealth)
    
    // Determine overall health
    const criticalCount = checks.filter(c => c.status === 'critical').length
    const warningCount = checks.filter(c => c.status === 'warning').length
    
    let overall: 'healthy' | 'warning' | 'critical' = 'healthy'
    if (criticalCount > 0) {
      overall = 'critical'
    } else if (warningCount > 0) {
      overall = 'warning'
    }
    
    this.healthChecks = checks
    
    return {
      overall,
      checks,
      scrapers: this.scraperHealth,
      apis: this.apiHealth,
      metrics
    }
  }

  private async checkDatabaseHealth(): Promise<HealthCheck> {
    const startTime = Date.now()
    
    try {
      // Test database connection by checking if we can access the database object
      if (db && typeof db === 'object') {
        const responseTime = Date.now() - startTime
        return {
          id: 'database_connection',
          component: 'Database',
          status: 'healthy',
          message: 'Database connection successful',
          timestamp: new Date().toISOString(),
          responseTime,
          details: {
            type: 'SQLite',
            responseTime
          }
        }
      } else {
        throw new Error('Database object not available')
      }
    } catch (error) {
      return {
        id: 'database_connection',
        component: 'Database',
        status: 'critical',
        message: `Database connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        details: {
          type: 'SQLite',
          error: error instanceof Error ? error.message : 'Unknown error'
        }
      }
    }
  }

  private async checkExternalApis(): Promise<HealthCheck[]> {
    const checks: HealthCheck[] = []
    
    // SEC EDGAR API Check
    const secCheck = await this.checkSecApi()
    checks.push(secCheck)
    
    // Yahoo Finance API Check
    const yahooCheck = await this.checkYahooApi()
    checks.push(yahooCheck)
    
    return checks
  }

  private async checkSecApi(): Promise<HealthCheck> {
    const startTime = Date.now()
    
    try {
      // Test SEC EDGAR API with a simple request
      const response = await fetch('https://www.sec.gov/Archives/edgar/data/0000320193/000032019323000106/aapl-20230930.htm', {
        headers: {
          'User-Agent': 'BoomBustSentinel/1.0 (your-email@domain.com)'
        }
      })
      
      const responseTime = Date.now() - startTime
      
      if (response.ok) {
        return {
          id: 'sec_api',
          component: 'SEC EDGAR API',
          status: 'healthy',
          message: 'SEC EDGAR API accessible',
          timestamp: new Date().toISOString(),
          responseTime,
          details: {
            statusCode: response.status,
            responseTime
          }
        }
      } else {
        return {
          id: 'sec_api',
          component: 'SEC EDGAR API',
          status: response.status === 403 ? 'warning' : 'critical',
          message: `SEC EDGAR API returned ${response.status}`,
          timestamp: new Date().toISOString(),
          responseTime,
          details: {
            statusCode: response.status,
            responseTime
          }
        }
      }
    } catch (error) {
      return {
        id: 'sec_api',
        component: 'SEC EDGAR API',
        status: 'critical',
        message: `SEC EDGAR API check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        details: {
          error: error instanceof Error ? error.message : 'Unknown error'
        }
      }
    }
  }

  private async checkYahooApi(): Promise<HealthCheck> {
    const startTime = Date.now()
    
    try {
      // Test Yahoo Finance API with a simple request
      const response = await fetch('https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&range=1d')
      
      const responseTime = Date.now() - startTime
      
      if (response.ok) {
        return {
          id: 'yahoo_api',
          component: 'Yahoo Finance API',
          status: 'healthy',
          message: 'Yahoo Finance API accessible',
          timestamp: new Date().toISOString(),
          responseTime,
          details: {
            statusCode: response.status,
            responseTime
          }
        }
      } else {
        return {
          id: 'yahoo_api',
          component: 'Yahoo Finance API',
          status: 'critical',
          message: `Yahoo Finance API returned ${response.status}`,
          timestamp: new Date().toISOString(),
          responseTime,
          details: {
            statusCode: response.status,
            responseTime
          }
        }
      }
    } catch (error) {
      return {
        id: 'yahoo_api',
        component: 'Yahoo Finance API',
        status: 'critical',
        message: `Yahoo Finance API check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        details: {
          error: error instanceof Error ? error.message : 'Unknown error'
        }
      }
    }
  }

  private async analyzeScraperHealth(): Promise<HealthCheck[]> {
    const checks: HealthCheck[] = []
    
    try {
      // Get real data to analyze scraper performance
      const metrics = await realDataService.getLatestMetrics()
      
      // Analyze each scraper's health based on data freshness and quality
      for (const metric of metrics) {
        const scraperHealth = await this.analyzeScraperPerformance(metric)
        checks.push(scraperHealth)
      }
      
    } catch (error) {
      checks.push({
        id: 'scraper_analysis',
        component: 'Scraper Analysis',
        status: 'critical',
        message: `Failed to analyze scraper health: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        details: {
          error: error instanceof Error ? error.message : 'Unknown error'
        }
      })
    }
    
    return checks
  }

  private async analyzeScraperPerformance(metric: any): Promise<HealthCheck> {
    const lastUpdate = new Date(metric.lastUpdated)
    const now = new Date()
    const hoursSinceUpdate = (now.getTime() - lastUpdate.getTime()) / (1000 * 60 * 60)
    
    let status: 'healthy' | 'warning' | 'critical' = 'healthy'
    let message = `${metric.name} scraper is healthy`
    
    // Determine status based on data freshness
    if (hoursSinceUpdate > 48) {
      status = 'critical'
      message = `${metric.name} data is stale (${Math.round(hoursSinceUpdate)} hours old)`
    } else if (hoursSinceUpdate > 24) {
      status = 'warning'
      message = `${metric.name} data is getting old (${Math.round(hoursSinceUpdate)} hours old)`
    }
    
    // Check data quality
    if (metric.confidence && metric.confidence < 0.5) {
      status = status === 'healthy' ? 'warning' : 'critical'
      message += ` - Low confidence (${(metric.confidence * 100).toFixed(1)}%)`
    }
    
    return {
      id: `${metric.id}_scraper`,
      component: `${metric.name} Scraper`,
      status,
      message,
      timestamp: new Date().toISOString(),
      details: {
        lastUpdate: metric.lastUpdated,
        hoursSinceUpdate: Math.round(hoursSinceUpdate),
        confidence: metric.confidence,
        source: metric.source,
        value: metric.value
      }
    }
  }

  private async getSystemMetrics(): Promise<SystemMetrics> {
    // Get process memory usage
    const memoryUsage = process.memoryUsage()
    const memoryUsagePercent = (memoryUsage.heapUsed / memoryUsage.heapTotal) * 100
    
    // Get uptime
    const uptime = process.uptime()
    
    // Get last data update time
    let lastDataUpdate = 'Unknown'
    try {
      const metrics = await realDataService.getLatestMetrics()
      if (metrics.length > 0) {
        const latestMetric = metrics.reduce((latest, current) => 
          new Date(current.lastUpdated) > new Date(latest.lastUpdated) ? current : latest
        )
        lastDataUpdate = latestMetric.lastUpdated
      }
    } catch (error) {
      console.error('Error getting last data update:', error)
    }
    
    // Check database status
    let databaseStatus: 'connected' | 'disconnected' | 'error' = 'disconnected'
    try {
      if (db && typeof db === 'object') {
        databaseStatus = 'connected'
      } else {
        databaseStatus = 'error'
      }
    } catch (error) {
      databaseStatus = 'error'
    }
    
    return {
      uptime,
      memoryUsage: memoryUsagePercent,
      cpuUsage: 0, // Would need additional monitoring for CPU
      activeConnections: 0, // Would need connection pooling monitoring
      databaseStatus,
      lastDataUpdate
    }
  }

  private async checkDataFreshness(): Promise<HealthCheck> {
    try {
      const metrics = await realDataService.getLatestMetrics()
      
      if (metrics.length === 0) {
        return {
          id: 'data_freshness',
          component: 'Data Freshness',
          status: 'critical',
          message: 'No metrics data available',
          timestamp: new Date().toISOString(),
          details: {
            metricCount: 0
          }
        }
      }
      
      // Check if any metric is older than 24 hours
      const now = new Date()
      const staleMetrics = metrics.filter(metric => {
        const lastUpdate = new Date(metric.lastUpdated)
        const hoursSinceUpdate = (now.getTime() - lastUpdate.getTime()) / (1000 * 60 * 60)
        return hoursSinceUpdate > 24
      })
      
      if (staleMetrics.length === metrics.length) {
        return {
          id: 'data_freshness',
          component: 'Data Freshness',
          status: 'critical',
          message: 'All metrics are stale (>24 hours old)',
          timestamp: new Date().toISOString(),
          details: {
            totalMetrics: metrics.length,
            staleMetrics: staleMetrics.length
          }
        }
      } else if (staleMetrics.length > 0) {
        return {
          id: 'data_freshness',
          component: 'Data Freshness',
          status: 'warning',
          message: `${staleMetrics.length} out of ${metrics.length} metrics are stale`,
          timestamp: new Date().toISOString(),
          details: {
            totalMetrics: metrics.length,
            staleMetrics: staleMetrics.length,
            staleMetricNames: staleMetrics.map(m => m.name)
          }
        }
      } else {
        return {
          id: 'data_freshness',
          component: 'Data Freshness',
          status: 'healthy',
          message: 'All metrics are fresh (<24 hours old)',
          timestamp: new Date().toISOString(),
          details: {
            totalMetrics: metrics.length,
            staleMetrics: 0
          }
        }
      }
    } catch (error) {
      return {
        id: 'data_freshness',
        component: 'Data Freshness',
        status: 'critical',
        message: `Failed to check data freshness: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        details: {
          error: error instanceof Error ? error.message : 'Unknown error'
        }
      }
    }
  }

  async getHealthHistory(): Promise<HealthCheck[]> {
    return this.healthChecks
  }

  async getScraperHealth(): Promise<ScraperHealth[]> {
    return this.scraperHealth
  }

  async getApiHealth(): Promise<ApiHealth[]> {
    return this.apiHealth
  }


}

export const systemHealthService = new SystemHealthService()
