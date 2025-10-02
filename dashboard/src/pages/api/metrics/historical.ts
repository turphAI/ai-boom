import { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  const days = parseInt(req.query.days as string) || 30;
  
  // Generate mock historical data
  const generateHistoricalData = (baseValue: number, volatility: number = 0.1) => {
    const data = [];
    const now = new Date();
    
    for (let i = days; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      // Add some realistic variation
      const variation = (Math.random() - 0.5) * volatility * baseValue;
      const value = baseValue + variation;
      
      data.push({
        timestamp: date.toISOString(),
        value: Math.max(0, value),
        date: date.toISOString().split('T')[0]
      });
    }
    
    return data;
  };

  const mockHistoricalData = {
    'bond_issuance': generateHistoricalData(3000000000, 0.3), // $3B base with 30% volatility
    'bdc_discount': generateHistoricalData(8.0, 0.2), // 8% base with 20% volatility
    'credit_fund': generateHistoricalData(120000000000, 0.05), // $120B base with 5% volatility
    'bank_provision': generateHistoricalData(11.5, 0.15), // 11.5% base with 15% volatility
    'correlation': generateHistoricalData(0.65, 0.1) // 0.65 base with 10% volatility
  };

  res.status(200).json({
    success: true,
    data: mockHistoricalData,
    period: `${days} days`,
    timestamp: new Date().toISOString()
  });
}