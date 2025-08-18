import { Client } from '@planetscale/database';
import { drizzle } from 'drizzle-orm/planetscale';
import * as schema from './schema';

// Always use PlanetScale (preferred)
const client = new Client({
  host: process.env.DATABASE_HOST,
  username: process.env.DATABASE_USERNAME,
  password: process.env.DATABASE_PASSWORD,
});

export const db = drizzle(client, { schema });

export type Database = typeof db;