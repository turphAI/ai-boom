import type { NextApiRequest, NextApiResponse } from 'next'
import { db } from '@/lib/db/connection'
import { metrics as metricsTable } from '@/lib/db/schema'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' })

  const auth = req.headers.authorization || ''
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : undefined
  const expected = process.env.AUTH_DEBUG_TOKEN || process.env.NEXTAUTH_SECRET
  if (!expected || token !== expected) return res.status(401).json({ error: 'Unauthorized' })

  try {
    const now = new Date()
    const rows = [
      { id: `bond_issuance_weekly_${Date.now()}`, dataSource: 'bond_issuance', metricName: 'weekly', value: '4800000000', unit: 'currency', status: 'warning', confidence: '0.95', metadata: {}, createdAt: now, updatedAt: now },
      { id: `bdc_discount_discount_to_nav_${Date.now()}`, dataSource: 'bdc_discount', metricName: 'discount_to_nav', value: '9.2', unit: 'percent', status: 'warning', confidence: '0.9', metadata: {}, createdAt: now, updatedAt: now },
      { id: `credit_fund_gross_asset_value_${Date.now()}`, dataSource: 'credit_fund', metricName: 'gross_asset_value', value: '90000000000', unit: 'currency', status: 'healthy', confidence: '0.9', metadata: {}, createdAt: now, updatedAt: now },
      { id: `bank_provision_non_bank_financial_provisions_${Date.now()}`, dataSource: 'bank_provision', metricName: 'non_bank_financial_provisions', value: '13.4', unit: 'percent', status: 'critical', confidence: '0.85', metadata: {}, createdAt: now, updatedAt: now },
    ]

    // Insert basic rows; ignore duplicates by best effort
    for (const r of rows) {
      await db.insert(metricsTable).values(r as any)
    }

    return res.status(200).json({ success: true, inserted: rows.length })
  } catch (error) {
    return res.status(500).json({ success: false, error: 'Seed failed' })
  }
}


