#!/usr/bin/env node

/**
 * Script to remove redundant indexes from PlanetScale database
 * Based on PlanetScale Insights recommendations
 * 
 * Usage:
 *   node scripts/remove-redundant-indexes.js
 * 
 * Environment variables:
 *   DATABASE_URL - PlanetScale connection string (required)
 */

const { Client } = require('@planetscale/database');
const fs = require('fs');
const path = require('path');

// Load environment variables
require('dotenv').config({ path: path.join(__dirname, '../.env.local') });
require('dotenv').config();

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
  console.error('❌ ERROR: DATABASE_URL environment variable is not set');
  console.error('Please set your PlanetScale connection string:');
  console.error("export DATABASE_URL='mysql://username:password@host/database?sslaccept=strict'");
  process.exit(1);
}

const client = new Client({
  url: DATABASE_URL,
});

async function executeSQL(sql) {
  const conn = client.connection();
  try {
    const result = await conn.execute(sql);
    return result;
  } catch (error) {
    // If index doesn't exist, that's okay - check for common error messages
    const errorMsg = error.message || '';
    if (errorMsg.includes("doesn't exist") || 
        errorMsg.includes("Unknown key") ||
        errorMsg.includes("check that column/key exists")) {
      return { success: true, skipped: true };
    }
    throw error;
  }
}

async function removeRedundantIndexes() {
  console.log('🚀 Starting removal of redundant indexes...\n');

  const migrationSQL = fs.readFileSync(
    path.join(__dirname, '../migrations/remove_redundant_indexes.sql'),
    'utf-8'
  );

  // Split by semicolon and filter out empty lines and comments
  const statements = migrationSQL
    .split(';')
    .map(s => {
      // Remove comments (lines starting with --) and trim
      const lines = s.split('\n')
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('--'))
        .join(' ')
        .trim();
      return lines;
    })
    .filter(s => s && s.length > 0 && s.toUpperCase().includes('ALTER TABLE'));

  const results = {
    success: [],
    skipped: [],
    errors: [],
  };

  for (const statement of statements) {
    // Extract index name and table name for logging
    const match = statement.match(/ALTER TABLE (\w+) DROP INDEX (\w+)/i);
    const tableName = match ? match[1] : 'unknown';
    const indexName = match ? match[2] : 'unknown';

    try {
      console.log(`📝 Dropping index: ${indexName} on ${tableName}...`);
      const result = await executeSQL(statement + ';');
      
      if (result.skipped) {
        console.log(`   ⏭️  Skipped (index doesn't exist)`);
        results.skipped.push({ index: indexName, table: tableName });
      } else {
        console.log(`   ✅ Successfully dropped`);
        results.success.push({ index: indexName, table: tableName });
      }
    } catch (error) {
      console.error(`   ❌ Error: ${error.message}`);
      results.errors.push({ 
        index: indexName, 
        table: tableName, 
        error: error.message 
      });
    }
  }

  console.log('\n📊 Summary:');
  console.log(`   ✅ Successfully removed: ${results.success.length}`);
  console.log(`   ⏭️  Skipped (didn't exist): ${results.skipped.length}`);
  console.log(`   ❌ Errors: ${results.errors.length}`);

  if (results.errors.length > 0) {
    console.log('\n❌ Errors encountered:');
    results.errors.forEach(({ index, table, error }) => {
      console.log(`   - ${index} on ${table}: ${error}`);
    });
    process.exit(1);
  }

  console.log('\n✅ Migration completed successfully!');
  console.log('\n💡 Note: These indexes were redundant because they duplicate');
  console.log('   primary keys, unique constraints, or other indexes.');
}

// Run the migration
removeRedundantIndexes()
  .then(() => {
    console.log('\n✨ Done!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n❌ Fatal error:', error);
    process.exit(1);
  });

