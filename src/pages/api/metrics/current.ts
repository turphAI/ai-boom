import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/config';
import { realDataService } from '@/lib/data/real-data-service';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    // Get real metrics data from scraper files
    const realMetrics = await realDataService.getLatestMetrics();
    
    if (realMetrics.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'No real data available. Please run the scrapers to collect data.',
        timestamp: new Date().toISOString()
      });
    }
    
    res.status(200).json({
      success: true,
      metrics: realMetrics,
      timestamp: new Date().toISOString(),
      note: 'Using real scraper data'
    });
  } catch (error) {
    console.error('Metrics error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch real data',
      timestamp: new Date().toISOString()
    });
  }
}





