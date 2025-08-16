import { NextApiRequest, NextApiResponse } from 'next'
import { alertTriggerService } from '@/lib/services/alert-trigger-service'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    try {
      // Evaluate all metrics against thresholds
      const triggers = await alertTriggerService.evaluateAlerts()
      
      res.status(200).json({
        success: true,
        triggers,
        timestamp: new Date().toISOString(),
        summary: {
          total: triggers.length,
          critical: triggers.filter(t => t.severity === 'critical').length,
          high: triggers.filter(t => t.severity === 'high').length,
          medium: triggers.filter(t => t.severity === 'medium').length,
          low: triggers.filter(t => t.severity === 'low').length
        }
      })
    } catch (error) {
      console.error('Error triggering alerts:', error)
      res.status(500).json({
        success: false,
        message: 'Failed to trigger alerts',
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  } else if (req.method === 'POST') {
    try {
      const { action, thresholdId, threshold } = req.body
      
      switch (action) {
        case 'update_threshold':
          await alertTriggerService.updateThreshold(threshold)
          res.status(200).json({
            success: true,
            message: 'Threshold updated successfully'
          })
          break
          
        case 'delete_threshold':
          await alertTriggerService.deleteThreshold(thresholdId)
          res.status(200).json({
            success: true,
            message: 'Threshold deleted successfully'
          })
          break
          
        default:
          res.status(400).json({
            success: false,
            message: 'Invalid action'
          })
      }
    } catch (error) {
      console.error('Error managing thresholds:', error)
      res.status(500).json({
        success: false,
        message: 'Failed to manage thresholds',
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  } else {
    res.status(405).json({ message: 'Method not allowed' })
  }
}
