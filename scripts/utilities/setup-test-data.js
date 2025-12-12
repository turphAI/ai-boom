#!/usr/bin/env node
/**
 * Setup test data for local development
 */

const bcrypt = require('bcryptjs');
const Database = require('better-sqlite3');
const crypto = require('crypto');
const uuidv4 = () => crypto.randomUUID();

async function setupTestData() {
  console.log('🚀 Setting up test data for Boom-Bust Sentinel dashboard...');
  
  // Create/connect to local SQLite database
  const db = new Database('./local.db');
  
  // Create tables (SQLite syntax)
  console.log('📊 Creating database tables...');
  
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      name TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);
  
  db.exec(`
    CREATE TABLE IF NOT EXISTS alert_configurations (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      data_source TEXT NOT NULL,
      metric_name TEXT NOT NULL,
      threshold_type TEXT NOT NULL,
      threshold_value DECIMAL(15,2) NOT NULL,
      comparison_period INTEGER NOT NULL,
      enabled BOOLEAN DEFAULT 1,
      notification_channels TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);
  
  db.exec(`
    CREATE TABLE IF NOT EXISTS user_preferences (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      preferences TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);
  
  // Create test users
  console.log('👤 Creating test users...');
  
  const testUsers = [
    {
      id: uuidv4(),
      email: 'demo@example.com',
      password: 'demo123',
      name: 'Demo User'
    },
    {
      id: uuidv4(),
      email: 'admin@example.com', 
      password: 'admin123',
      name: 'Admin User'
    }
  ];
  
  const insertUser = db.prepare(`
    INSERT OR REPLACE INTO users (id, email, password_hash, name, created_at, updated_at)
    VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
  `);
  
  for (const user of testUsers) {
    const hashedPassword = await bcrypt.hash(user.password, 10);
    insertUser.run(user.id, user.email, hashedPassword, user.name);
    console.log(`   ✅ Created user: ${user.email} (password: ${user.password})`);
  }
  
  // Create sample alert configurations
  console.log('🔔 Creating sample alert configurations...');
  
  const sampleAlerts = [
    {
      id: uuidv4(),
      userId: testUsers[0].id,
      dataSource: 'bond_issuance',
      metricName: 'weekly',
      thresholdType: 'absolute',
      thresholdValue: 5000000000, // $5B
      comparisonPeriod: 7,
      enabled: true,
      notificationChannels: JSON.stringify(['email', 'dashboard'])
    },
    {
      id: uuidv4(),
      userId: testUsers[0].id,
      dataSource: 'bdc_discount',
      metricName: 'average_discount',
      thresholdType: 'percentage_change',
      thresholdValue: 0.05, // 5%
      comparisonPeriod: 1,
      enabled: true,
      notificationChannels: JSON.stringify(['dashboard'])
    },
    {
      id: uuidv4(),
      userId: testUsers[1].id,
      dataSource: 'credit_fund',
      metricName: 'asset_marks',
      thresholdType: 'percentage_change',
      thresholdValue: 0.10, // 10%
      comparisonPeriod: 30,
      enabled: false,
      notificationChannels: JSON.stringify(['email'])
    }
  ];
  
  const insertAlert = db.prepare(`
    INSERT OR REPLACE INTO alert_configurations 
    (id, user_id, data_source, metric_name, threshold_type, threshold_value, comparison_period, enabled, notification_channels, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
  `);
  
  for (const alert of sampleAlerts) {
    insertAlert.run(
      alert.id, alert.userId, alert.dataSource, alert.metricName,
      alert.thresholdType, alert.thresholdValue, alert.comparisonPeriod,
      alert.enabled ? 1 : 0, alert.notificationChannels
    );
    console.log(`   ✅ Created alert: ${alert.dataSource}.${alert.metricName}`);
  }
  
  // Create user preferences
  console.log('⚙️ Creating user preferences...');
  
  const insertPrefs = db.prepare(`
    INSERT OR REPLACE INTO user_preferences (id, user_id, preferences, created_at, updated_at)
    VALUES (?, ?, ?, datetime('now'), datetime('now'))
  `);
  
  const demoPrefs = {
    theme: 'light',
    timezone: 'America/New_York',
    defaultChartPeriod: 30,
    emailNotifications: true
  };
  
  insertPrefs.run(uuidv4(), testUsers[0].id, JSON.stringify(demoPrefs));
  
  db.close();
  
  console.log('\n🎉 Test data setup complete!');
  console.log('\n📋 Test Accounts:');
  console.log('   Email: demo@example.com');
  console.log('   Password: demo123');
  console.log('');
  console.log('   Email: admin@example.com');
  console.log('   Password: admin123');
  console.log('\n🚀 Start the dashboard: npm run dev');
  console.log('   Then go to: http://localhost:3000');
}

// Add uuid function if crypto.randomUUID is not available
if (!require('crypto').randomUUID) {
  require('crypto').randomUUID = function() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  };
}

setupTestData().catch(console.error);