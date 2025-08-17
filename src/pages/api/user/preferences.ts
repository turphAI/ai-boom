import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/config';
import { db } from '@/lib/db/connection';
import { userPreferences } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';
import { z } from 'zod';

const preferencesSchema = z.object({
  theme: z.enum(['light', 'dark']).optional(),
  timezone: z.string().optional(),
  defaultChartPeriod: z.number().min(1).max(365).optional(),
  emailNotifications: z.boolean().optional(),
  slackWebhook: z.string().url().optional(),
  telegramBotToken: z.string().optional(),
  telegramChatId: z.string().optional(),
});

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
      case 'PUT':
        return await handlePut(req, res, userId);
      default:
        return res.status(405).json({ error: 'Method not allowed' });
    }
  } catch (error) {
    console.error('User preferences error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

async function handleGet(req: NextApiRequest, res: NextApiResponse, userId: string) {
  const preferences = await db
    .select()
    .from(userPreferences)
    .where(eq(userPreferences.userId, userId))
    .limit(1);

  if (preferences.length === 0) {
    // Return default preferences
    const defaultPrefs = {
      theme: 'light' as const,
      timezone: 'UTC',
      defaultChartPeriod: 30,
      emailNotifications: true,
    };
    return res.status(200).json({ preferences: defaultPrefs });
  }

  const parsedPrefs = preferences[0].preferences ? JSON.parse(preferences[0].preferences) : {};
  res.status(200).json({ preferences: parsedPrefs });
}

async function handlePut(req: NextApiRequest, res: NextApiResponse, userId: string) {
  const validatedPreferences = preferencesSchema.parse(req.body);

  // Check if preferences exist
  const existing = await db
    .select()
    .from(userPreferences)
    .where(eq(userPreferences.userId, userId))
    .limit(1);

  if (existing.length === 0) {
    // Create new preferences
    const prefId = crypto.randomUUID();
    await db.insert(userPreferences).values({
      id: prefId,
      userId,
      preferences: JSON.stringify(validatedPreferences),
    });
  } else {
    // Update existing preferences
    const currentPrefs = existing[0].preferences ? JSON.parse(existing[0].preferences) : {};
    const updatedPrefs = { ...currentPrefs, ...validatedPreferences };
    
    await db
      .update(userPreferences)
      .set({ preferences: JSON.stringify(updatedPrefs) })
      .where(eq(userPreferences.userId, userId));
  }

  // Return updated preferences
  const updated = await db
    .select()
    .from(userPreferences)
    .where(eq(userPreferences.userId, userId))
    .limit(1);

  const parsedPrefs = updated[0].preferences ? JSON.parse(updated[0].preferences) : {};
  res.status(200).json({ preferences: parsedPrefs });
}