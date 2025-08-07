import { NextApiRequest, NextApiResponse } from 'next'
import { getServerSession } from 'next-auth/next'
import { authOptions } from '@/lib/auth/config'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const session = await getServerSession(req, res, authOptions)
    if (!session) {
      return res.status(401).json({ error: 'Unauthorized' })
    }

    // Mock system health data - in production this would query actual system status
    const healthData = [
      {
        dataSource: 'Bond Issuance Scraper',
        status: 'healthy' as const,
        lastUpdate: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
        uptime: 86400 * 7, // 7 days in seconds
      },
      {
        dataSource: 'BDC Discount Scraper',
        status: 'healthy' as const,
        lastUpdate: new Date(Date.now() - 1000 * 60 * 45).toISOString(), // 45 minutes ago
        uptime: 86400 * 5, // 5 days in seconds
      },
      {
        dataSource: 'Credit Fund Scraper',
        status: 'degraded' as const,
        lastUpdate: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(), // 3 hours ago
        uptime: 86400 * 2, // 2 days in seconds
        errorMessage: 'Form PF data delayed from SEC',
      },
      {
        dataSource: 'Bank Provision Scraper',
        status: 'healthy' as const,
        lastUpdate: new Date(Date.now() - 1000 * 60 * 15).toISOString(), // 15 minutes ago
        uptime: 86400 * 10, // 10 days in seconds
      },
    ]

    res.status(200).json({ health: healthData })
  } catch (error) {
    console.error('System health API error:', error)
    res.status(500).json({ error: 'Internal server error' })
  }
}