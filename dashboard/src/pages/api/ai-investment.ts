import { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

interface AIInvestmentData {
  ticker: string;
  name: string;
  category: string;
  rd: number | null;
  rd_formatted: string;
  rd_period: string | null;
  capex: number | null;
  capex_abs: number | null;
  capex_formatted: string;
  capex_period: string | null;
  capex_multiplier: number;
  ai_investment_proxy: number | null;
  ai_investment_formatted: string;
  calculation: {
    formula: string;
    rd_component: number;
    capex_component: number;
  };
  timestamp: string;
}

interface Methodology {
  description: string;
  formula: string;
  data_sources: string[];
  multipliers: {
    tech_companies: string;
    data_centers: string;
    financial: string;
  };
  limitations: string[];
}

interface AIInvestmentResponse {
  success: boolean;
  data?: {
    total_ai_investment: number;
    total_ai_investment_formatted: string;
    ticker_count: number;
    individual_tickers: Record<string, AIInvestmentData>;
    category_totals: Record<string, any>;
    timestamp: string;
    data_quality: string;
    methodology: Methodology;
  };
  error?: string;
  timestamp: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<AIInvestmentResponse>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
      timestamp: new Date().toISOString()
    });
  }

  try {
    // Try to read AI investment data from the data directory
    const dataDir = path.join(process.cwd(), '..', 'data');
    const aiInvestmentFile = path.join(dataDir, 'ai_investment_data.json');

    let aiInvestmentData: any = null;

    // Check if the file exists
    if (fs.existsSync(aiInvestmentFile)) {
      const fileContent = fs.readFileSync(aiInvestmentFile, 'utf-8');
      const parsed = JSON.parse(fileContent);
      
      // The file contains an array of data points, get the most recent one
      if (Array.isArray(parsed) && parsed.length > 0) {
        aiInvestmentData = parsed[0].data || parsed[0];
      } else if (parsed.individual_tickers) {
        aiInvestmentData = parsed;
      }
    }

    if (!aiInvestmentData || !aiInvestmentData.individual_tickers) {
      // No data available yet - return empty state with methodology
      return res.status(200).json({
        success: true,
        data: {
          total_ai_investment: 0,
          total_ai_investment_formatted: '-',
          ticker_count: 0,
          individual_tickers: {},
          category_totals: {},
          timestamp: new Date().toISOString(),
          data_quality: 'no_data',
          methodology: {
            description: 'AI Investment Proxy calculated from R&D spending and weighted CapEx',
            formula: 'AI Investment Proxy = R&D + (CapEx × category_multiplier)',
            data_sources: ['Yahoo Finance Income Statement (R&D)', 'Yahoo Finance Cash Flow (CapEx)'],
            multipliers: {
              tech_companies: '60-90% of CapEx',
              data_centers: '70-90% of CapEx',
              financial: '20-40% of CapEx'
            },
            limitations: [
              'Not all R&D is AI-related',
              'CapEx includes non-AI infrastructure',
              'Based on most recent annual figures',
              'Multipliers are estimates based on industry analysis'
            ]
          }
        },
        timestamp: new Date().toISOString()
      });
    }

    // Return the AI investment data
    res.status(200).json({
      success: true,
      data: {
        total_ai_investment: aiInvestmentData.total_ai_investment || 0,
        total_ai_investment_formatted: aiInvestmentData.total_ai_investment_formatted || '-',
        ticker_count: aiInvestmentData.ticker_count || 0,
        individual_tickers: aiInvestmentData.individual_tickers || {},
        category_totals: aiInvestmentData.category_totals || {},
        timestamp: aiInvestmentData.timestamp || new Date().toISOString(),
        data_quality: aiInvestmentData.metadata?.data_quality || 'unknown',
        methodology: aiInvestmentData.metadata?.methodology || {
          description: 'AI Investment Proxy calculated from R&D spending and weighted CapEx',
          formula: 'AI Investment Proxy = R&D + (CapEx × category_multiplier)',
          data_sources: ['Yahoo Finance Income Statement (R&D)', 'Yahoo Finance Cash Flow (CapEx)'],
          multipliers: {
            tech_companies: '60-90% of CapEx',
            data_centers: '70-90% of CapEx',
            financial: '20-40% of CapEx'
          },
          limitations: [
            'Not all R&D is AI-related',
            'CapEx includes non-AI infrastructure',
            'Based on most recent annual figures',
            'Multipliers are estimates based on industry analysis'
          ]
        }
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Error fetching AI investment data:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to fetch AI investment data',
      timestamp: new Date().toISOString()
    });
  }
}

