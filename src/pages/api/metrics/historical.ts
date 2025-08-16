import { NextApiRequest, NextApiResponse } from 'next';
import { realDataService } from '@/lib/data/real-data-service';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  const days = parseInt(req.query.days as string) || 30;
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);

  try {
    // Get real historical data
    const realHistoricalData = await getRealHistoricalData(days);
    
    res.status(200).json({
      success: true,
      data: realHistoricalData,
      period: `${days} days`,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching historical data:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to fetch historical data',
      period: `${days} days`,
      timestamp: new Date().toISOString()
    });
  }
}

async function getRealHistoricalData(days: number) {
  try {
    const metricKeys = ['bond_issuance', 'bdc_discount', 'credit_fund', 'bank_provision'];
    const historicalData: Record<string, any[]> = {};

    for (const metricKey of metricKeys) {
      const data = await realDataService.getHistoricalData(metricKey, days);
      if (data.length > 0) {
        historicalData[metricKey] = data;
      }
    }

    return historicalData;
  } catch (error) {
    console.error('Error getting real historical data:', error);
    return {};
  }
}