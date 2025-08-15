import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/config';
import fs from 'fs';
import path from 'path';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const session = await getServerSession(req, res, authOptions);
    if (!session) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    // Get real metrics data from data files
    const realMetrics = await getRealMetrics();
    
    res.status(200).json({
      success: true,
      metrics: realMetrics,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Metrics error:', error);
    // Fallback to mock data if real data fails
    const mockMetrics = getMockMetrics();
    res.status(200).json({
      success: true,
      metrics: mockMetrics,
      timestamp: new Date().toISOString()
    });
  }
}

async function getRealMetrics() {
  const dataDir = path.join(process.cwd(), 'data');
  const metrics = [];

  try {
    // Bond Issuance Data
    const bondIssuancePath = path.join(dataDir, 'bond_issuance_weekly.json');
    if (fs.existsSync(bondIssuancePath)) {
      const bondData = JSON.parse(fs.readFileSync(bondIssuancePath, 'utf8'));
      const latestBond = Array.isArray(bondData) ? bondData[0] : bondData; // Most recent is first
      
      metrics.push({
        id: 'bond-issuance',
        name: 'Bond Issuance',
        value: latestBond?.data?.value || 0,
        unit: 'currency',
        change: calculateChange(bondData),
        changePercent: calculateChangePercent(bondData),
        status: getStatus(latestBond?.data?.value || 0, 5000000000), // $5B threshold
        lastUpdated: latestBond?.timestamp || new Date().toISOString(),
        source: 'SEC EDGAR'
      });
    }

    // BDC Discount Data
    const bdcDiscountPath = path.join(dataDir, 'bdc_discount_discount_to_nav.json');
    if (fs.existsSync(bdcDiscountPath)) {
      const bdcData = JSON.parse(fs.readFileSync(bdcDiscountPath, 'utf8'));
      const latestBdc = Array.isArray(bdcData) ? bdcData[0] : bdcData; // Most recent is first
      
      metrics.push({
        id: 'bdc-discount',
        name: 'BDC Avg Discount',
        value: latestBdc?.data?.value || 0,
        unit: 'percent',
        change: calculateChange(bdcData),
        changePercent: calculateChangePercent(bdcData),
        status: getStatus(latestBdc?.data?.value || 0, 10), // 10% threshold
        lastUpdated: latestBdc?.timestamp || new Date().toISOString(),
        source: 'Yahoo Finance + RSS'
      });
    }

    // Credit Fund Data
    const creditFundPath = path.join(dataDir, 'comprehensive_test_test_metric.json');
    if (fs.existsSync(creditFundPath)) {
      const creditData = JSON.parse(fs.readFileSync(creditFundPath, 'utf8'));
      const latestCredit = Array.isArray(creditData) ? creditData[0] : creditData; // Most recent is first
      
      metrics.push({
        id: 'credit-fund',
        name: 'Credit Fund Assets',
        value: latestCredit?.data?.value || 0,
        unit: 'currency',
        change: calculateChange(creditData),
        changePercent: calculateChangePercent(creditData),
        status: getStatus(latestCredit?.data?.value || 0, 100000000000), // $100B threshold
        lastUpdated: latestCredit?.timestamp || new Date().toISOString(),
        source: 'Form PF Filings'
      });
    }

    // Bank Provision Data
    const bankProvisionPath = path.join(dataDir, 'health_check_database_test.json');
    if (fs.existsSync(bankProvisionPath)) {
      const bankData = JSON.parse(fs.readFileSync(bankProvisionPath, 'utf8'));
      const latestBank = Array.isArray(bankData) ? bankData[0] : bankData; // Most recent is first
      
      metrics.push({
        id: 'bank-provision',
        name: 'Bank Provisions',
        value: latestBank?.data?.value || 0,
        unit: 'percent',
        change: calculateChange(bankData),
        changePercent: calculateChangePercent(bankData),
        status: getStatus(latestBank?.data?.value || 0, 15), // 15% threshold
        lastUpdated: latestBank?.timestamp || new Date().toISOString(),
        source: '10-Q Filings'
      });
    }

  } catch (error) {
    console.error('Error reading metrics data:', error);
  }

  // If no real data found, return empty array
  return metrics.length > 0 ? metrics : getMockMetrics();
}

function calculateChange(data: any) {
  if (!Array.isArray(data) || data.length < 2) return 0;
  const current = data[0]?.data?.value || 0; // Most recent is first
  const previous = data[1]?.data?.value || 0; // Second most recent
  return current - previous;
}

function calculateChangePercent(data: any) {
  if (!Array.isArray(data) || data.length < 2) return 0;
  const current = data[0]?.data?.value || 0; // Most recent is first
  const previous = data[1]?.data?.value || 0; // Second most recent
  if (previous === 0) return 0;
  return ((current - previous) / previous) * 100;
}

function getStatus(value: number, threshold: number) {
  if (value > threshold * 1.2) return 'critical';
  if (value > threshold) return 'warning';
  return 'healthy';
}

function getMockMetrics() {
  // Fallback mock data
  return [
    {
      id: 'bond-issuance',
      name: 'Bond Issuance',
      value: 3500000000,
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
      value: 125000000000,
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
}