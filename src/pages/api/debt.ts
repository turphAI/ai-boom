import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

interface DebtData {
  ticker: string;
  name: string;
  category: string;
  total_debt: number | null;
  total_debt_formatted: string;
  long_term_debt: number | null;
  long_term_debt_formatted: string;
  current_debt: number | null;
  current_debt_formatted: string;
  debt_to_equity: number | null;
  period: string | null;
  timestamp: string;
}

interface DebtMethodology {
  description: string;
  metrics: {
    total_debt: string;
    long_term_debt: string;
    current_debt: string;
  };
  data_sources: string[];
  notes: string[];
}

interface DebtResponse {
  success: boolean;
  data?: {
    total_debt: number;
    total_debt_formatted: string;
    ticker_count: number;
    individual_tickers: Record<string, DebtData>;
    category_totals: Record<string, any>;
    timestamp: string;
    data_quality: string;
    methodology: DebtMethodology;
  };
  error?: string;
  timestamp: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<DebtResponse>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
      timestamp: new Date().toISOString()
    });
  }

  try {
    // Try to read debt data from the data directory
    const dataDir = path.join(process.cwd(), '..', 'data');
    const debtFile = path.join(dataDir, 'debt_data.json');

    let debtData: any = null;

    // Check if the file exists
    if (fs.existsSync(debtFile)) {
      const fileContent = fs.readFileSync(debtFile, 'utf-8');
      const parsed = JSON.parse(fileContent);
      
      // The file contains an array of data points, get the most recent one
      if (Array.isArray(parsed) && parsed.length > 0) {
        debtData = parsed[0].data || parsed[0];
      } else if (parsed.individual_tickers) {
        debtData = parsed;
      }
    }

    const defaultMethodology: DebtMethodology = {
      description: 'Total debt outstanding from company balance sheets',
      metrics: {
        total_debt: 'Combined short-term and long-term debt obligations',
        long_term_debt: 'Bonds, notes, and borrowings due after one year',
        current_debt: 'Short-term borrowings and current portion of long-term debt'
      },
      data_sources: [
        'Yahoo Finance Balance Sheet',
        'Most recent quarterly filing (10-Q) or annual filing (10-K)'
      ],
      notes: [
        'Represents debt on the balance sheet, not lending capacity',
        'For banks/BDCs, this is their own borrowings, not loans made to others',
        'Updated quarterly with company filings',
        'Does not include off-balance-sheet obligations'
      ]
    };

    if (!debtData || !debtData.individual_tickers) {
      // No data available yet - return empty state with methodology
      return res.status(200).json({
        success: true,
        data: {
          total_debt: 0,
          total_debt_formatted: '-',
          ticker_count: 0,
          individual_tickers: {},
          category_totals: {},
          timestamp: new Date().toISOString(),
          data_quality: 'no_data',
          methodology: defaultMethodology
        },
        timestamp: new Date().toISOString()
      });
    }

    // Return the debt data
    res.status(200).json({
      success: true,
      data: {
        total_debt: debtData.total_debt || 0,
        total_debt_formatted: debtData.total_debt_formatted || '-',
        ticker_count: debtData.ticker_count || 0,
        individual_tickers: debtData.individual_tickers || {},
        category_totals: debtData.category_totals || {},
        timestamp: debtData.timestamp || new Date().toISOString(),
        data_quality: debtData.metadata?.data_quality || 'unknown',
        methodology: debtData.metadata?.methodology || defaultMethodology
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Error fetching debt data:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to fetch debt data',
      timestamp: new Date().toISOString()
    });
  }
}

