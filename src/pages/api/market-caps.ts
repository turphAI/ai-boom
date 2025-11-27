import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

interface MarketCapData {
  ticker: string;
  name: string;
  category: string;
  market_cap: number;
  market_cap_formatted: string;
  price?: number;
  currency: string;
  timestamp: string;
}

interface MarketCapResponse {
  success: boolean;
  data?: {
    total_market_cap: number;
    total_market_cap_formatted: string;
    ticker_count: number;
    individual_tickers: Record<string, MarketCapData>;
    category_totals: Record<string, { total: number; formatted: string }>;
    timestamp: string;
    data_quality: string;
  };
  error?: string;
  timestamp: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<MarketCapResponse>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
      timestamp: new Date().toISOString()
    });
  }

  try {
    // Try to read market cap data from the data directory
    const dataDir = path.join(process.cwd(), '..', 'data');
    // Check both file naming conventions
    let marketCapFile = path.join(dataDir, 'market_cap_data.json');
    if (!fs.existsSync(marketCapFile)) {
      marketCapFile = path.join(dataDir, 'market_cap_daily.json');
    }

    let marketCapData: any = null;

    // Check if the file exists
    if (fs.existsSync(marketCapFile)) {
      const fileContent = fs.readFileSync(marketCapFile, 'utf-8');
      const parsed = JSON.parse(fileContent);
      
      // The file contains an array of data points, get the most recent one
      if (Array.isArray(parsed) && parsed.length > 0) {
        marketCapData = parsed[0].data || parsed[0];
      } else if (parsed.individual_tickers) {
        marketCapData = parsed;
      }
    }

    if (!marketCapData || !marketCapData.individual_tickers) {
      // No data available yet - return empty state
      return res.status(200).json({
        success: true,
        data: {
          total_market_cap: 0,
          total_market_cap_formatted: '-',
          ticker_count: 0,
          individual_tickers: {},
          category_totals: {},
          timestamp: new Date().toISOString(),
          data_quality: 'no_data'
        },
        timestamp: new Date().toISOString()
      });
    }

    // Return the market cap data
    res.status(200).json({
      success: true,
      data: {
        total_market_cap: marketCapData.total_market_cap || 0,
        total_market_cap_formatted: marketCapData.total_market_cap_formatted || '-',
        ticker_count: marketCapData.ticker_count || 0,
        individual_tickers: marketCapData.individual_tickers || {},
        category_totals: marketCapData.category_totals || {},
        timestamp: marketCapData.timestamp || new Date().toISOString(),
        data_quality: marketCapData.metadata?.data_quality || 'unknown'
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Error fetching market cap data:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to fetch market cap data',
      timestamp: new Date().toISOString()
    });
  }
}

