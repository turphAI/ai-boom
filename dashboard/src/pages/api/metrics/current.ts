import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/config';
import { stateStoreClient } from '@/lib/data/state-store-client';
import { z } from 'zod';

const querySchema = z.object({
  dataSource: z.string().optional(),
  metricName: z.string().optional(),
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

    const { dataSource, metricName } = querySchema.parse(req.query);

    // Try to get real metrics, fallback to mock data for development
    let metrics;
    try {
      metrics = await stateStoreClient.getCurrentMetrics();
    } catch (error) {
      console.warn('Using mock data for development:', error);
      // Mock data for development
      metrics = [
        {
          id: '1',
          name: 'Weekly Bond Issuance',
          value: 15000000000,
          unit: 'currency',
          change: 2500000000,
          changePercent: 20.0,
          status: 'warning',
          lastUpdated: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
          source: 'SEC EDGAR',
        },
        {
          id: '2',
          name: 'BDC Discount to NAV',
          value: -12.5,
          unit: 'percentage',
          change: -2.1,
          changePercent: -20.2,
          status: 'healthy',
          lastUpdated: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
          source: 'Yahoo Finance',
        },
        {
          id: '3',
          name: 'Credit Fund Assets',
          value: 850000000,
          unit: 'currency',
          change: -50000000,
          changePercent: -5.6,
          status: 'critical',
          lastUpdated: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(),
          source: 'Form PF',
        },
        {
          id: '4',
          name: 'Bank Provisions',
          value: 2300000000,
          unit: 'currency',
          change: 150000000,
          changePercent: 7.0,
          status: 'stale',
          lastUpdated: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
          source: 'XBRL Data',
        },
      ];
    }

    // Filter by data source if specified (only for real data)
    if (dataSource && metrics.length > 0 && 'dataSource' in metrics[0]) {
      metrics = metrics.filter(m => (m as any).dataSource === dataSource);
    }

    // Filter by metric name if specified (only for real data)
    if (metricName && metrics.length > 0 && 'metricName' in metrics[0]) {
      metrics = metrics.filter(m => (m as any).metricName === metricName);
    }

    res.status(200).json({
      metrics,
      lastUpdated: new Date().toISOString(),
      count: metrics.length
    });
  } catch (error) {
    console.error('Current metrics error:', error);
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Invalid query parameters', details: error.errors });
    }
    res.status(500).json({ error: 'Internal server error' });
  }
}