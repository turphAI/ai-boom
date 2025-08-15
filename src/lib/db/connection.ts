import { connect } from '@planetscale/database';
import { drizzle } from 'drizzle-orm/planetscale-serverless';
import Database from 'better-sqlite3';
import { drizzle as drizzleSqlite } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

// Use SQLite for local development and Vercel deployment, PlanetScale for production
let db: any;

if (process.env.NODE_ENV === 'development' || process.env.VERCEL) {
  // Local SQLite setup or Vercel deployment
  const sqlite = new Database('./local.db'); // Use file-based database for local development
  db = drizzleSqlite(sqlite, { schema });
  
  // Initialize the database with tables and test data
  if (process.env.VERCEL) {
    // Create tables and test user for Vercel deployment
    sqlite.exec(`
      CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
      
      INSERT OR REPLACE INTO users (id, email, password_hash, name) 
      VALUES (
        'demo-user-id',
        'demo@example.com',
        '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', -- password: demo123
        'Demo User'
      );
    `);
  }
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