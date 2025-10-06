import { NextApiRequest, NextApiResponse } from 'next';
import { realDataService } from '../../../lib/data/real-data-service';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    // Get real metrics data instead of mock data
    const metrics = await realDataService.getLatestMetrics();
    
    // Ensure all expected metric IDs are represented so UI can render cards
    const expected = ['bond_issuance', 'bdc_discount', 'credit_fund', 'bank_provision', 'correlation'];
    const byId: Record<string, any> = {};
    for (const m of metrics) {
      if (m && m.id) byId[m.id] = m;
    }
    const normalized = expected.map((id) => byId[id] || { id, name: id.replace('_',' '), value: null, change: null, lastUpdated: null, unit: null });
    
    res.status(200).json({
      success: true,
      metrics: normalized,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching current metrics:', error);
    
    // Return a proper JSON response even on error to prevent HTML 404 pages
    res.status(500).json({
      success: false,
      error: 'Failed to fetch metrics',
      metrics: [],
      timestamp: new Date().toISOString()
    });
  }
}