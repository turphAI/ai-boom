import { NextApiRequest, NextApiResponse } from 'next';
import { realDataService } from '../../../lib/data/real-data-service';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    // Get real metrics data instead of mock data
    const metrics = await realDataService.getLatestMetrics();
    console.log('🔍 API Debug - Raw metrics from realDataService:', metrics.length, 'metrics');
    console.log('🔍 API Debug - First metric:', metrics[0]);
    
    // Ensure all expected metric IDs are represented so UI can render cards
    const expected = ['bond_issuance', 'bdc_discount', 'credit_fund', 'bank_provision', 'correlation'];
    const byId: Record<string, any> = {};
    for (const m of metrics) {
      if (m && m.id) byId[m.id] = m;
    }
    let normalized = expected.map((id) => byId[id] || { id, name: id.replace('_',' '), value: null, change: null, lastUpdated: null, unit: null });
    
    // If no current values available from DB, fall back to latest historical points
    const hasAnyValue = normalized.some(m => m && m.value !== null && m.value !== undefined);
    if (!hasAnyValue) {
      const unitMapping: Record<string, string> = {
        bond_issuance: 'currency',
        bdc_discount: 'percent',
        credit_fund: 'currency',
        bank_provision: 'percent',
        correlation: 'ratio',
      };
      const filled: any[] = [];
      for (const id of expected) {
        try {
          const hist = await realDataService.getHistoricalData(id, 30);
          const last = Array.isArray(hist) && hist.length > 0 ? hist[hist.length - 1] : null;
          if (last) {
            filled.push({
              id,
              name: id.replace('_', ' '),
              value: last.value,
              change: 0,
              lastUpdated: last.timestamp,
              unit: unitMapping[id] || null,
            });
          } else {
            filled.push({ id, name: id.replace('_',' '), value: null, change: null, lastUpdated: null, unit: null });
          }
        } catch (e) {
          filled.push({ id, name: id.replace('_',' '), value: null, change: null, lastUpdated: null, unit: null });
        }
      }
      normalized = filled;
    }

    console.log('🔍 API Debug - Normalized metrics:', normalized.length, 'metrics');
    console.log('🔍 API Debug - First normalized metric:', normalized[0]);
    
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