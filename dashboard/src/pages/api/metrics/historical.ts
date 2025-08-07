import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/config';
import { stateStoreClient, HistoricalDataPoint } from '@/lib/data/state-store-client';
import { z } from 'zod';

interface HistoricalMetric {
  dataSource: string;
  metricName: string;
  data: HistoricalDataPoint[];
  aggregation: {
    avg: number;
    min: number;
    max: number;
    trend: 'up' | 'down' | 'stable';
    changePercent: number;
  };
}

const calculateAggregation = (data: HistoricalDataPoint[]) => {
  if (data.length === 0) {
    return { avg: 0, min: 0, max: 0, trend: 'stable' as const, changePercent: 0 };
  }
  
  const values = data.map(d => d.value);
  const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
  const min = Math.min(...values);
  const max = Math.max(...values);
  
  // Calculate trend based on first and last values
  const firstValue = values[0];
  const lastValue = values[values.length - 1];
  const changePercent = ((lastValue - firstValue) / Math.abs(firstValue)) * 100;
  
  let trend: 'up' | 'down' | 'stable' = 'stable';
  if (Math.abs(changePercent) > 5) {
    trend = changePercent > 0 ? 'up' : 'down';
  }
  
  return {
    avg: Math.round(avg * 100) / 100,
    min: Math.round(min * 100) / 100,
    max: Math.round(max * 100) / 100,
    trend,
    changePercent: Math.round(changePercent * 100) / 100
  };
};

const querySchema = z.object({
  days: z.string().transform(val => parseInt(val)).default('30'),
  aggregation: z.enum(['daily', 'weekly', 'monthly']).default('daily'),
});

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const session = await getServerSession(req, res, authOptions);
    if (!session) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const { days, aggregation } = querySchema.parse(req.query);

    // Validate days range
    if (days < 1 || days > 365) {
      return res.status(400).json({ error: 'Days must be between 1 and 365' });
    }

    // Try to get real data, fallback to mock data for development
    let historicalData;
    try {
      // This would normally fetch from multiple data sources
      historicalData = await stateStoreClient.getHistoricalData('bond_issuance', 'weekly', days);
    } catch (error) {
      console.warn('Using mock historical data for development:', error);
      // Generate mock historical data
      const generateMockData = (name: string, baseValue: number, volatility: number) => {
        const data = [];
        for (let i = days; i >= 0; i--) {
          const date = new Date();
          date.setDate(date.getDate() - i);
          const randomVariation = (Math.random() - 0.5) * volatility;
          data.push({
            timestamp: date.toISOString(),
            value: baseValue + randomVariation,
          });
        }
        return data;
      };

      historicalData = {
        bond_issuance: generateMockData('Bond Issuance', 12000000000, 3000000000),
        bdc_discount: generateMockData('BDC Discount', -10.5, 5),
        credit_fund_assets: generateMockData('Credit Fund Assets', 900000000, 100000000),
        bank_provisions: generateMockData('Bank Provisions', 2000000000, 300000000),
      };
    }

    res.status(200).json({
      data: historicalData,
      aggregation,
      days,
      lastUpdated: new Date().toISOString()
    });
  } catch (error) {
    console.error('Historical metrics error:', error);
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Invalid query parameters', details: error.errors });
    }
    res.status(500).json({ error: 'Internal server error' });
  }
}