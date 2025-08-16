import { NextApiRequest, NextApiResponse } from 'next';
import { db } from '@/lib/db/connection';
import { metricsData } from '@/lib/db/schema';
import { eq, gte, desc } from 'drizzle-orm';
import { realDataService } from '@/lib/data/real-data-service';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  const days = parseInt(req.query.days as string) || 30;
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);

  try {
    // Try to get real historical data first
    const realHistoricalData = await getRealHistoricalData(days);
    
    if (Object.keys(realHistoricalData).length > 0) {
      res.status(200).json({
        success: true,
        data: realHistoricalData,
        period: `${days} days`,
        timestamp: new Date().toISOString()
      });
      return;
    }

    // Fallback to database
    const historicalData = await db
      .select()
      .from(metricsData)
      .where(gte(metricsData.timestamp, cutoffDate.toISOString()))
      .orderBy(desc(metricsData.timestamp));

    // Group data by metric type
    const groupedData: Record<string, any[]> = {
      bond_issuance: [],
      bdc_discount: [],
      credit_fund: [],
      bank_provision: []
    };

    historicalData.forEach((record: any) => {
      const metricKey = record.metricName.toLowerCase().replace(/\s+/g, '_');
      if (groupedData[metricKey]) {
        groupedData[metricKey].push({
          timestamp: record.timestamp,
          value: record.value,
          date: record.timestamp.split('T')[0]
        });
      }
    });

    // Sort each metric by timestamp and filter by appropriate frequency
    Object.keys(groupedData).forEach(key => {
      groupedData[key].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
      
      // For quarterly metrics, only show quarterly data points
      if (key === 'credit_fund' || key === 'bank_provision') {
        const quarterlyData: any[] = [];
        const seenQuarters = new Set();
        
        groupedData[key].forEach(point => {
          const date = new Date(point.timestamp);
          const year = date.getFullYear();
          const quarter = Math.floor(date.getMonth() / 3) + 1;
          const quarterKey = `${year}-Q${quarter}`;
          
          // Only include the latest data point for each quarter
          if (!seenQuarters.has(quarterKey)) {
            seenQuarters.add(quarterKey);
            quarterlyData.push(point);
          }
        });
        
        groupedData[key] = quarterlyData;
      }
    });

    res.status(200).json({
      success: true,
      data: groupedData,
      period: `${days} days`,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching historical data:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to fetch historical data',
      period: `${days} days`,
      timestamp: new Date().toISOString()
    });
  }
}

async function getRealHistoricalData(days: number) {
  try {
    const metricKeys = ['bond_issuance', 'bdc_discount', 'credit_fund', 'bank_provision'];
    const historicalData: Record<string, any[]> = {};

    for (const metricKey of metricKeys) {
      const data = await realDataService.getHistoricalData(metricKey, days);
      if (data.length > 0) {
        historicalData[metricKey] = data;
      }
    }

    return historicalData;
  } catch (error) {
    console.error('Error getting real historical data:', error);
    return {};
  }
}