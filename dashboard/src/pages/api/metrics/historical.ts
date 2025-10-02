import { NextApiRequest, NextApiResponse } from 'next';
import { realDataService } from '../../../lib/data/real-data-service';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  const days = parseInt(req.query.days as string) || 30;
  
  try {
    // Get real historical data from the data service
    const historicalData: Record<string, any[]> = {};
    
    // Get historical data for each metric
    const metrics = ['bond_issuance', 'bdc_discount', 'credit_fund', 'bank_provision'];
    
    for (const metric of metrics) {
      const data = await realDataService.getHistoricalData(metric, days);
      // Only include metrics that have data
      if (data.length > 0) {
        historicalData[metric] = data;
      }
    }
    
    // Add correlation metric (calculated from other metrics)
    const correlationData = await realDataService.getHistoricalData('correlation', days);
    if (correlationData.length > 0) {
      historicalData['correlation'] = correlationData;
    }

    res.status(200).json({
      success: true,
      data: historicalData,
      period: `${days} days`,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching historical data:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch historical data',
      data: {}
    });
  }
}