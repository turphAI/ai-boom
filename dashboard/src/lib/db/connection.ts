import { Client } from '@planetscale/database';
import { drizzle } from 'drizzle-orm/planetscale-serverless';
import * as schema from './schema';

// Prefer explicit env vars; otherwise, parse DATABASE_URL
function resolvePlanetScaleConfig(): { host: string; username: string; password: string } {
  // Prefer DATABASE_URL to avoid mismatches when both are set
  const url = process.env.DATABASE_URL;
  if (url && url.startsWith('mysql://')) {
    const parsed = new URL(url);
    return {
      host: parsed.hostname,
      username: decodeURIComponent(parsed.username),
      password: decodeURIComponent(parsed.password),
    };
  }

  const host = process.env.DATABASE_HOST;
  const username = process.env.DATABASE_USERNAME;
  const password = process.env.DATABASE_PASSWORD;

  if (host && username && password) {
    return { host, username, password };
  }

  throw new Error('Database configuration missing: set DATABASE_URL or DATABASE_HOST/USERNAME/PASSWORD');
}

const client = new Client(resolvePlanetScaleConfig());

export const db = drizzle(client, { schema });

export type Database = typeof db;