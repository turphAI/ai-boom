import { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  // Mock system health data
  const mockHealthData = [
    {
      component: 'Bond Issuance Scraper',
      status: 'healthy',
      lastCheck: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutes ago
      responseTime: 1250,
      successRate: 98.5,
      errorCount: 2,
      details: 'Last execution: 3.5B bonds processed'
    },
    {
      component: 'BDC Discount Scraper',
      status: 'degraded',
      lastCheck: new Date(Date.now() - 15 * 60 * 1000).toISOString(), // 15 minutes ago
      responseTime: 3200,
      successRate: 85.2,
      errorCount: 8,
      details: 'Some RSS feeds returning 404'
    },
    {
      component: 'Credit Fund Scraper',
      status: 'healthy',
      lastCheck: new Date(Date.now() - 2 * 60 * 1000).toISOString(), // 2 minutes ago
      responseTime: 890,
      successRate: 99.1,
      errorCount: 0,
      details: 'All Form PF filings processed'
    },
    {
      component: 'Bank Provision Scraper',
      status: 'failed',
      lastCheck: new Date(Date.now() - 45 * 60 * 1000).toISOString(), // 45 minutes ago
      responseTime: null,
      successRate: 45.0,
      errorCount: 15,
      details: 'SEC.gov rate limiting detected'
    },
    {
      component: 'Database',
      status: 'healthy',
      lastCheck: new Date(Date.now() - 1 * 60 * 1000).toISOString(), // 1 minute ago
      responseTime: 45,
      successRate: 100.0,
      errorCount: 0,
      details: 'SQLite local database operational'
    },
    {
      component: 'Alert System',
      status: 'healthy',
      lastCheck: new Date(Date.now() - 3 * 60 * 1000).toISOString(), // 3 minutes ago
      responseTime: 120,
      successRate: 97.8,
      errorCount: 1,
      details: '3 alerts sent in last 24h'
    }
  ];

  // Calculate overall system health
  const healthyCount = mockHealthData.filter(h => h.status === 'healthy').length;
  const totalCount = mockHealthData.length;
  const overallHealth = (healthyCount / totalCount) * 100;

  res.status(200).json({
    success: true,
    health: mockHealthData,
    summary: {
      overallHealth: Math.round(overallHealth),
      healthyComponents: healthyCount,
      totalComponents: totalCount,
      lastUpdated: new Date().toISOString()
    },
    timestamp: new Date().toISOString()
  });
}