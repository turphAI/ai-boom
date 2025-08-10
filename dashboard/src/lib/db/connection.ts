import { connect } from '@planetscale/database';
import { drizzle } from 'drizzle-orm/planetscale-serverless';
import Database from 'better-sqlite3';
import { drizzle as drizzleSqlite } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

// Use SQLite for local development, PlanetScale for production
let db: any;

if (process.env.NODE_ENV === 'development' && !process.env.DATABASE_URL?.includes('mysql')) {
  // Local SQLite setup
  const sqlite = new Database('./local.db');
  db = drizzleSqlite(sqlite, { schema });
} else {
  // PlanetScale production setup
  const connection = connect({
    host: process.env.DATABASE_HOST,
    username: process.env.DATABASE_USERNAME,
    password: process.env.DATABASE_PASSWORD,
  });
  db = drizzle(connection, { schema });
}

export { db };

export type Database = typeof db;