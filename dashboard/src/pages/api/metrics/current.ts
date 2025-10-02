import { NextApiRequest, NextApiResponse } from 'next';
import { realDataService } from '../../../lib/data/real-data-service';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    // Get real metrics data instead of mock data
    const metrics = await realDataService.getLatestMetrics();
    
    res.status(200).json({
      success: true,
      metrics: metrics,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching current metrics:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch metrics',
      metrics: []
    });
  }
}