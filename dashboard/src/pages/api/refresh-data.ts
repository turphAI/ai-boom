import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/config';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const session = await getServerSession(req, res, authOptions);
    if (!session) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    // Set the FRED API key
    process.env.FRED_API_KEY = 'fba11235c90a241910f0b42d1f8dfb8e';

    // Execute the data refresh script
    const projectRoot = process.cwd().replace('/dashboard', '');
    const scriptPath = `${projectRoot}/scripts/refresh_real_data.py`;
    
    console.log('Refreshing data with script:', scriptPath);
    
    const { stdout, stderr } = await execAsync(`cd ${projectRoot} && source venv/bin/activate && python ${scriptPath}`, {
      timeout: 30000 // 30 second timeout
    });

    if (stderr && !stderr.includes('Warning')) {
      console.error('Data refresh stderr:', stderr);
      return res.status(500).json({ 
        success: false, 
        error: 'Data refresh failed',
        details: stderr
      });
    }

    console.log('Data refresh output:', stdout);

    res.status(200).json({
      success: true,
      message: 'Data refreshed successfully',
      output: stdout,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Data refresh error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to refresh data',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
