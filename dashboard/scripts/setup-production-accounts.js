#!/usr/bin/env node
/**
 * Setup test accounts for production PlanetScale database
 */

const bcrypt = require('bcryptjs');
const { drizzle } = require('drizzle-orm/mysql2');
const mysql = require('mysql2/promise');

async function setupProductionAccounts() {
  console.log('🚀 Setting up test accounts for production database...');
  
  // Load environment variables
  require('dotenv').config({ path: '.env.local' });
  
  // Database connection
  const connection = await mysql.createConnection({
    host: process.env.DATABASE_HOST,
    user: process.env.DATABASE_USERNAME,
    password: process.env.DATABASE_PASSWORD,
    database: process.env.DATABASE_NAME || 'boom_bust_sentinel',
    ssl: { rejectUnauthorized: false }
  });

  const db = drizzle(connection);

  try {
    // Create test users
    console.log('👤 Creating test users...');
    
    const testUsers = [
      {
        email: 'admin@example.com',
        password: 'admin123',
        name: 'Admin User'
      },
      {
        email: 'demo@example.com',
        password: 'demo123',
        name: 'Demo User'
      }
    ];

    for (const user of testUsers) {
      const hashedPassword = await bcrypt.hash(user.password, 10);
      
      // Check if user already exists
      const [existingUsers] = await connection.execute(
        'SELECT id FROM users WHERE email = ?',
        [user.email]
      );

      if (existingUsers.length > 0) {
        console.log(`   ⚠️  User already exists: ${user.email}`);
        continue;
      }

      // Insert new user
      await connection.execute(
        'INSERT INTO users (email, password_hash, name, created_at, updated_at) VALUES (?, ?, ?, NOW(), NOW())',
        [user.email, hashedPassword, user.name]
      );
      
      console.log(`   ✅ Created user: ${user.email} (password: ${user.password})`);
    }

    console.log('\n🎉 Production accounts setup complete!');
    console.log('\n📋 Test Accounts:');
    console.log('   Email: admin@example.com');
    console.log('   Password: admin123');
    console.log('');
    console.log('   Email: demo@example.com');
    console.log('   Password: demo123');
    console.log('\n🌐 Try logging in at: https://ai-boom-iota.vercel.app');

  } catch (error) {
    console.error('❌ Error setting up accounts:', error);
  } finally {
    await connection.end();
  }
}

setupProductionAccounts().catch(console.error);
