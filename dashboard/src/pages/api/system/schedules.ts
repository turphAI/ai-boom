import { NextApiRequest, NextApiResponse } from 'next';
import { getSchedules } from '@/lib/schedules';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const schedules = getSchedules();

    res.status(200).json({
      success: true,
      schedules,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching schedules:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch schedules',
      timestamp: new Date().toISOString()
    });
  }
}

