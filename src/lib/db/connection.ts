import { Client } from '@planetscale/database';
import { drizzle } from 'drizzle-orm/planetscale-serverless';
import * as schema from './schema';

// Use PlanetScale Client instance
const client = new Client({
  url: process.env.DATABASE_URL!,
});

const db = drizzle(client, { schema });

export { db };

export type Database = typeof db;