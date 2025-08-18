import type { Config } from 'drizzle-kit';
import { config as loadEnv } from 'dotenv';
import { existsSync } from 'fs';

// Load env for CLI: prefer .env.local (Next dev) then fallback to .env
if (existsSync('.env.local')) {
  loadEnv({ path: '.env.local' });
} else {
  loadEnv();
}

export default {
  schema: './src/lib/db/schema.ts',
  out: './drizzle',
  dialect: 'mysql',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
} satisfies Config;
