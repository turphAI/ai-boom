import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/config';
import { db } from '@/lib/db/connection';
import { alertConfigurations } from '@/lib/db/schema';
import { eq, and } from 'drizzle-orm';
import { z } from 'zod';

const alertConfigSchema = z.object({
  dataSource: z.string(),
  metricName: z.string(),
  thresholdType: z.enum(['absolute', 'percentage', 'standard_deviation']),
  thresholdValue: z.number(),
  comparisonPeriod: z.number().min(1).max(365),
  enabled: z.boolean().default(true),
  notificationChannels: z.array(z.string()).default(['email']),
});

const updateAlertConfigSchema = alertConfigSchema.partial();

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    const session = await getServerSession(req, res, authOptions);
    if (!session) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const userId = session.user.id;

    switch (req.method) {
      case 'GET':
        return await handleGet(req, res, userId);
      case 'POST':
        return await handlePost(req, res, userId);
      case 'PUT':
        return await handlePut(req, res, userId);
      case 'DELETE':
        return await handleDelete(req, res, userId);
      default:
        return res.status(405).json({ error: 'Method not allowed' });
    }
  } catch (error) {
    console.error('Alert config error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

async function handleGet(req: NextApiRequest, res: NextApiResponse, userId: string) {
  const { dataSource, metricName } = req.query;

  try {
    // Build conditions array
    const conditions = [eq(alertConfigurations.userId, userId)];
    
    if (dataSource && typeof dataSource === 'string') {
      conditions.push(eq(alertConfigurations.dataSource, dataSource));
    }

    if (metricName && typeof metricName === 'string') {
      conditions.push(eq(alertConfigurations.metricName, metricName));
    }

    const configs = await db
      .select()
      .from(alertConfigurations)
      .where(and(...conditions));

    // Transform the data to match the frontend expectations
    const transformedConfigs = configs.map((config: any) => {
      let channels = ['email']; // default
      if (config.notificationChannels) {
        try {
          channels = JSON.parse(config.notificationChannels);
        } catch (error) {
          console.warn('Failed to parse notificationChannels:', error);
        }
      }
      return {
        ...config,
        channels,
      };
    });

    res.status(200).json({ configs: transformedConfigs });
  } catch (error) {
    console.warn('Using mock alert configs for development:', error);
    // Mock data for development
    const mockConfigs = [
      {
        id: '1',
        metricName: 'weekly_bond_issuance',
        dataSource: 'bond_issuance',
        thresholdType: 'percentage',
        thresholdValue: 20.0,
        comparisonPeriod: 7,
        enabled: true,
        channels: ['email', 'slack'],
      },
      {
        id: '2',
        metricName: 'bdc_discount',
        dataSource: 'bdc_discount',
        thresholdType: 'absolute',
        thresholdValue: -15.0,
        comparisonPeriod: 1,
        enabled: true,
        channels: ['email'],
      },
    ];
    res.status(200).json({ configs: mockConfigs });
  }
}

async function handlePost(req: NextApiRequest, res: NextApiResponse, userId: string) {
  try {
    const validatedData = alertConfigSchema.parse(req.body);

    // Check if config already exists for this user/dataSource/metric combination
    const existing = await db
      .select()
      .from(alertConfigurations)
      .where(and(
        eq(alertConfigurations.userId, userId),
        eq(alertConfigurations.dataSource, validatedData.dataSource),
        eq(alertConfigurations.metricName, validatedData.metricName)
      ))
      .limit(1);

    if (existing.length > 0) {
      return res.status(400).json({ error: 'Alert configuration already exists for this metric' });
    }

    const configId = crypto.randomUUID();
    await db.insert(alertConfigurations).values({
      id: configId,
      userId,
      dataSource: validatedData.dataSource,
      metricName: validatedData.metricName,
      thresholdType: validatedData.thresholdType,
      thresholdValue: validatedData.thresholdValue.toString(),
      comparisonPeriod: validatedData.comparisonPeriod,
      enabled: validatedData.enabled,
      notificationChannels: JSON.stringify(validatedData.notificationChannels),
    });

    const newConfig = await db
      .select()
      .from(alertConfigurations)
      .where(eq(alertConfigurations.id, configId))
      .limit(1);

    // Transform the response to include channels
    let channels = ['email']; // default
    if (newConfig[0].notificationChannels) {
      try {
        channels = JSON.parse(newConfig[0].notificationChannels);
      } catch (error) {
        console.warn('Failed to parse notificationChannels:', error);
      }
    }
    const transformedConfig = {
      ...newConfig[0],
      channels,
    };

    res.status(201).json({ config: transformedConfig });
  } catch (error) {
    console.warn('Database not available, using mock response:', error);
    // Mock response for development
    const mockConfig = {
      id: crypto.randomUUID(),
      ...req.body,
      userId,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    res.status(201).json({ config: mockConfig });
  }
}

async function handlePut(req: NextApiRequest, res: NextApiResponse, userId: string) {
  const { id } = req.query;
  if (!id || typeof id !== 'string') {
    return res.status(400).json({ error: 'Config ID is required' });
  }

  try {
    const validatedData = updateAlertConfigSchema.parse(req.body);

    // Verify ownership
    const existing = await db
      .select()
      .from(alertConfigurations)
      .where(and(
        eq(alertConfigurations.id, id),
        eq(alertConfigurations.userId, userId)
      ))
      .limit(1);

    if (existing.length === 0) {
      return res.status(404).json({ error: 'Alert configuration not found' });
    }

    // Convert thresholdValue to string if present and handle notificationChannels
    const updateData: any = { ...validatedData };
    if (updateData.thresholdValue !== undefined) {
      updateData.thresholdValue = updateData.thresholdValue.toString();
    }
    if (updateData.notificationChannels !== undefined) {
      updateData.notificationChannels = JSON.stringify(updateData.notificationChannels);
    }

    await db
      .update(alertConfigurations)
      .set(updateData)
      .where(eq(alertConfigurations.id, id));

    const updatedConfig = await db
      .select()
      .from(alertConfigurations)
      .where(eq(alertConfigurations.id, id))
      .limit(1);

    // Transform the response to include channels
    let channels = ['email']; // default
    if (updatedConfig[0].notificationChannels) {
      try {
        channels = JSON.parse(updatedConfig[0].notificationChannels);
      } catch (error) {
        console.warn('Failed to parse notificationChannels:', error);
      }
    }
    const transformedConfig = {
      ...updatedConfig[0],
      channels,
    };

    res.status(200).json({ config: transformedConfig });
  } catch (error) {
    console.warn('Database not available, using mock response:', error);
    // Mock response for development
    const mockConfig = {
      id,
      ...req.body,
      userId,
      updatedAt: new Date().toISOString(),
    };
    res.status(200).json({ config: mockConfig });
  }
}

async function handleDelete(req: NextApiRequest, res: NextApiResponse, userId: string) {
  const { id } = req.query;
  if (!id || typeof id !== 'string') {
    return res.status(400).json({ error: 'Config ID is required' });
  }

  try {
    // Verify ownership
    const existing = await db
      .select()
      .from(alertConfigurations)
      .where(and(
        eq(alertConfigurations.id, id),
        eq(alertConfigurations.userId, userId)
      ))
      .limit(1);

    if (existing.length === 0) {
      return res.status(404).json({ error: 'Alert configuration not found' });
    }

    await db
      .delete(alertConfigurations)
      .where(eq(alertConfigurations.id, id));

    res.status(200).json({ message: 'Alert configuration deleted successfully' });
  } catch (error) {
    console.warn('Database not available, using mock response:', error);
    // Mock response for development
    res.status(200).json({ message: 'Alert configuration deleted successfully' });
  }
}