// Client to connect to the existing state store (DynamoDB/Firestore)
// This integrates with the existing StateStore from the main system

interface MetricValue {
  dataSource: string;
  metricName: string;
  value: number;
  timestamp: string;
  confidence: number;
  metadata: Record<string, any>;
}

interface HistoricalDataPoint {
  timestamp: string;
  value: number;
  confidence: number;
  metadata?: Record<string, any>;
}

class StateStoreClient {
  private tableName: string;

  constructor() {
    this.tableName = process.env.STATE_STORE_TABLE || 'market_metrics';
  }

  // Mock implementation - in production this would connect to actual DynamoDB/Firestore
  async getCurrentMetrics(): Promise<MetricValue[]> {
    // This would query the actual state store table
    // For now, return mock data that matches the expected format
    return [
      {
        dataSource: 'bond_issuance',
        metricName: 'weekly',
        value: 12500000000,
        timestamp: new Date().toISOString(),
        confidence: 0.95,
        metadata: {
          companies: ['MSFT', 'META', 'AMZN'],
          avgCoupon: 4.25,
          source: 'sec_edgar'
        }
      },
      {
        dataSource: 'bdc_discount',
        metricName: 'average_discount',
        value: -0.08,
        timestamp: new Date().toISOString(),
        confidence: 0.92,
        metadata: {
          bdcs: ['ARCC', 'OCSL', 'MAIN', 'PSEC'],
          priceSource: 'yahoo_finance'
        }
      },
      {
        dataSource: 'credit_fund',
        metricName: 'asset_value_change',
        value: -0.12,
        timestamp: new Date().toISOString(),
        confidence: 0.88,
        metadata: {
          quarter: 'Q4-2023',
          source: 'form_pf'
        }
      },
      {
        dataSource: 'bank_provision',
        metricName: 'non_bank_provision_change',
        value: 0.23,
        timestamp: new Date().toISOString(),
        confidence: 0.90,
        metadata: {
          banks: ['JPM', 'BAC', 'WFC'],
          source: 'xbrl'
        }
      }
    ];
  }

  async getHistoricalData(
    dataSource: string,
    metricName: string,
    days: number = 30
  ): Promise<HistoricalDataPoint[]> {
    // Mock historical data generation
    const data: HistoricalDataPoint[] = [];
    const now = new Date();
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      // Generate realistic mock data based on data source
      let baseValue = 0;
      let variance = 0;
      
      switch (dataSource) {
        case 'bond_issuance':
          baseValue = 10000000000;
          variance = 5000000000;
          break;
        case 'bdc_discount':
          baseValue = -0.05;
          variance = 0.03;
          break;
        case 'credit_fund':
          baseValue = 0;
          variance = 0.15;
          break;
        case 'bank_provision':
          baseValue = 0.1;
          variance = 0.2;
          break;
      }
      
      const randomFactor = (Math.random() - 0.5) * 2;
      const value = baseValue + (variance * randomFactor);
      
      data.push({
        timestamp: date.toISOString(),
        value: Math.round(value * 100) / 100,
        confidence: 0.85 + (Math.random() * 0.15),
        metadata: {
          dayOfWeek: date.getDay(),
          source: 'mock_data'
        }
      });
    }
    
    return data;
  }

  async getMetricsByDataSource(dataSource: string): Promise<MetricValue[]> {
    const allMetrics = await this.getCurrentMetrics();
    return allMetrics.filter(m => m.dataSource === dataSource);
  }
}

export const stateStoreClient = new StateStoreClient();
export type { MetricValue, HistoricalDataPoint };