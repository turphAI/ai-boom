import { NextApiRequest, NextApiResponse } from 'next'
import { db } from '@/lib/db/connection'
import { alertConfigurations } from '@/lib/db/schema'
import { eq, desc } from 'drizzle-orm'
import { alertTriggerService } from '@/lib/services/alert-trigger-service'

// Mock alert history data for development
const mockAlerts = [
  {
    id: '1',
    type: 'threshold_breach',
    dataSource: 'bond_issuance',
    metricName: 'Bond Issuance',
    message: 'Weekly bond issuance exceeded $5B threshold',
    severity: 'high' as const,
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    acknowledged: false
  },
  {
    id: '2',
    type: 'threshold_breach',
    dataSource: 'credit_fund',
    metricName: 'Credit Fund Assets',
    message: 'Credit fund assets dropped 15% from previous quarter',
    severity: 'critical' as const,
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(), // 6 hours ago
    acknowledged: true
  },
  {
    id: '3',
    type: 'data_staleness',
    dataSource: 'bdc_discount',
    metricName: 'BDC Discount',
    message: 'BDC discount data is 48 hours old',
    severity: 'medium' as const,
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
    acknowledged: false
  }
]

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    try {
      // Get real-time triggered alerts
      const triggers = await alertTriggerService.evaluateAlerts()
      
      // Convert triggers to alert format
      const realAlerts = triggers.map(trigger => ({
        id: trigger.id,
        type: 'threshold_breach',
        dataSource: trigger.metricKey,
        metricName: trigger.metricKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        message: trigger.message,
        severity: trigger.severity,
        timestamp: trigger.timestamp,
        acknowledged: false
      }))
      
      // Combine with mock alerts for now
      const allAlerts = [...realAlerts, ...mockAlerts]
      
      res.status(200).json({
        success: true,
        alerts: allAlerts,
        timestamp: new Date().toISOString(),
        note: realAlerts.length > 0 ? 'Includes real-time triggered alerts' : 'Using mock data only'
      })
    } catch (error) {
      console.error('Error fetching alert history:', error)
      res.status(500).json({
        success: false,
        message: 'Failed to fetch alert history',
        alerts: []
      })
    }
  } else if (req.method === 'PUT') {
    // Acknowledge an alert
    try {
      const { id } = req.body
      
      // TODO: Update alert status in database
      console.log(`Acknowledging alert: ${id}`)
      
      res.status(200).json({
        success: true,
        message: 'Alert acknowledged'
      })
    } catch (error) {
      console.error('Error acknowledging alert:', error)
      res.status(500).json({
        success: false,
        message: 'Failed to acknowledge alert'
      })
    }
  } else if (req.method === 'DELETE') {
    // Dismiss an alert
    try {
      const { id } = req.query
      
      // TODO: Remove alert from database
      console.log(`Dismissing alert: ${id}`)
      
      res.status(200).json({
        success: true,
        message: 'Alert dismissed'
      })
    } catch (error) {
      console.error('Error dismissing alert:', error)
      res.status(500).json({
        success: false,
        message: 'Failed to dismiss alert'
      })
    }
  } else {
    res.status(405).json({ message: 'Method not allowed' })
  }
}
