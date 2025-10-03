import type { NextApiRequest, NextApiResponse } from 'next';
// Note: load DB connection lazily inside the handler so we can surface
// configuration errors (e.g., missing DATABASE_* env) in the response.
import { users } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';
import bcrypt from 'bcryptjs';

type Data =
  | { error: string; details?: string }
  | {
      ok: true;
      usersCount: number;
      emailChecked?: string;
      userFound?: boolean;
      passwordValid?: boolean;
    };

export default async function handler(req: NextApiRequest, res: NextApiResponse<Data>) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const authHeader = req.headers.authorization || '';
  const headerToken = authHeader.startsWith('Bearer ')
    ? authHeader.substring('Bearer '.length)
    : undefined;
  const queryToken = typeof req.query.token === 'string' ? (req.query.token as string) : undefined;
  const token = headerToken || queryToken;
  const expected = process.env.AUTH_DEBUG_TOKEN || process.env.NEXTAUTH_SECRET;

  if (!expected || token !== expected) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    // Dynamically import the DB to catch configuration errors
    const { db } = await import('@/lib/db/connection');
    const allUsers = await db.select({ id: users.id }).from(users).limit(100);
    const usersCount = allUsers.length;

    const email = (req.query.email as string | undefined)?.toLowerCase();
    const password = req.query.password as string | undefined;

    if (!email) {
      return res.status(200).json({ ok: true, usersCount });
    }

    const found = await db.select().from(users).where(eq(users.email, email)).limit(1);
    const userFound = found.length > 0;

    if (!userFound) {
      return res.status(200).json({ ok: true, usersCount, emailChecked: email, userFound: false });
    }

    let passwordValid: boolean | undefined = undefined;
    if (password) {
      passwordValid = await bcrypt.compare(password, found[0].passwordHash);
    }

    return res.status(200).json({
      ok: true,
      usersCount,
      emailChecked: email,
      userFound,
      passwordValid,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return res.status(500).json({ error: 'Internal server error', details: message });
  }
}


