import { Client } from '@planetscale/database';
import { drizzle } from 'drizzle-orm/planetscale-serverless';
import * as schema from './schema';

// Prefer explicit env vars; otherwise, parse DATABASE_URL
function resolvePlanetScaleConfig(): { host: string; username: string; password: string } {
  const host = process.env.DATABASE_HOST;
  const username = process.env.DATABASE_USERNAME;
  const password = process.env.DATABASE_PASSWORD;

  if (host && username && password) {
    return { host, username, password };
  }

  const url = process.env.DATABASE_URL;
  if (url && url.startsWith('mysql://')) {
    const parsed = new URL(url);
    return {
      host: parsed.hostname,
      username: decodeURIComponent(parsed.username),
      password: decodeURIComponent(parsed.password),
    };
  }

  throw new Error('Database configuration missing: set DATABASE_HOST/USERNAME/PASSWORD or DATABASE_URL');
}

const client = new Client(resolvePlanetScaleConfig());

export const db = drizzle(client, { schema });

export type Database = typeof db;