import { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  // Mock current metrics data
  const mockMetrics = [
    {
      id: 'bond-issuance',
      name: 'Bond Issuance',
      value: 3500000000, // $3.5B
      unit: 'currency',
      change: 15.2,
      changePercent: 15.2,
      status: 'healthy',
      lastUpdated: new Date().toISOString(),
      source: 'SEC EDGAR'
    },
    {
      id: 'bdc-discount',
      name: 'BDC Avg Discount',
      value: 8.5,
      unit: 'percent',
      change: -2.1,
      changePercent: -2.1,
      status: 'warning',
      lastUpdated: new Date().toISOString(),
      source: 'Yahoo Finance + RSS'
    },
    {
      id: 'credit-fund',
      name: 'Credit Fund Assets',
      value: 125000000000, // $125B
      unit: 'currency',
      change: 3.8,
      changePercent: 3.8,
      status: 'healthy',
      lastUpdated: new Date().toISOString(),
      source: 'Form PF Filings'
    },
    {
      id: 'bank-provision',
      name: 'Bank Provisions',
      value: 12.3,
      unit: 'percent',
      change: 0.5,
      changePercent: 0.5,
      status: 'critical',
      lastUpdated: new Date().toISOString(),
      source: '10-Q Filings'
    }
  ];

  res.status(200).json({
    success: true,
    metrics: mockMetrics,
    timestamp: new Date().toISOString()
  });
}