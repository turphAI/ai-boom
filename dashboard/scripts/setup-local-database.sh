#!/bin/bash

# Local Database Setup Script for Boom-Bust Sentinel Dashboard
# This script sets up a local development database and creates initial data

set -e

echo "🚀 Setting up local database for Boom-Bust Sentinel Dashboard..."

# Check if required environment variables are set
if [ -z "$DATABASE_URL" ] && [ -z "$DATABASE_HOST" ]; then
    echo "⚠️  No database configuration found. Setting up local MySQL..."
    
    # Check if MySQL is installed
    if ! command -v mysql &> /dev/null; then
        echo "❌ MySQL not found. Please install MySQL:"
        echo "   brew install mysql  # macOS"
        echo "   sudo apt-get install mysql-server  # Ubuntu"
        echo "   Or use Docker: docker run --name mysql-dev -e MYSQL_ROOT_PASSWORD=password -p 3306:3306 -d mysql:8.0"
        exit 1
    fi
    
    # Start MySQL service
    echo "🔄 Starting MySQL service..."
    if command -v brew &> /dev/null; then
        brew services start mysql
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start mysql
    fi
    
    # Create database and user
    echo "📊 Creating database and user..."
    mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS boom_bust_sentinel;
CREATE USER IF NOT EXISTS 'sentinel_user'@'localhost' IDENTIFIED BY 'sentinel_password';
GRANT ALL PRIVILEGES ON boom_bust_sentinel.* TO 'sentinel_user'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    # Set local environment variables
    export DATABASE_URL="mysql://sentinel_user:sentinel_password@localhost:3306/boom_bust_sentinel?sslaccept=strict"
    export DATABASE_HOST="localhost"
    export DATABASE_USERNAME="sentinel_user"
    export DATABASE_PASSWORD="sentinel_password"
    
    echo "✅ Local database created successfully!"
    echo "   Database: boom_bust_sentinel"
    echo "   User: sentinel_user"
    echo "   Password: sentinel_password"
    echo ""
    echo "Add these to your .env.local file:"
    echo "DATABASE_URL=mysql://sentinel_user:sentinel_password@localhost:3306/boom_bust_sentinel?sslaccept=strict"
fi

# Generate database schema
echo "📝 Generating database migrations..."
npm run db:generate

# Push schema to database
echo "🔄 Pushing schema to database..."
npm run db:push

# Create initial user for testing
echo "👤 Creating initial test user..."
node -e "
const bcrypt = require('bcryptjs');
const { db } = require('./src/lib/db/connection');
const { users } = require('./src/lib/db/schema');

async function createTestUser() {
  try {
    const hashedPassword = await bcrypt.hash('testpassword123', 12);
    await db.insert(users).values({
      email: 'test@example.com',
      passwordHash: hashedPassword,
      name: 'Test User',
      role: 'admin',
      emailVerified: true
    });
    console.log('✅ Test user created: test@example.com / testpassword123');
  } catch (error) {
    if (error.message.includes('Duplicate entry')) {
      console.log('ℹ️  Test user already exists');
    } else {
      console.error('❌ Error creating test user:', error.message);
    }
  }
}

createTestUser();
"

# Seed initial metrics data
echo "📊 Seeding initial metrics data..."
node -e "
const { db } = require('./src/lib/db/connection');
const { metrics } = require('./src/lib/db/schema');

async function seedMetrics() {
  try {
    const now = new Date();
    const seedData = [
      {
        id: 'bond_issuance_weekly_seed',
        dataSource: 'bond_issuance',
        metricName: 'weekly',
        value: '4800000000',
        unit: 'currency',
        status: 'warning',
        confidence: '0.95',
        metadata: JSON.stringify({ source: 'seeded_data', companies: ['MSFT', 'META', 'AMZN'] }),
        createdAt: now,
        updatedAt: now
      },
      {
        id: 'bdc_discount_discount_to_nav_seed',
        dataSource: 'bdc_discount',
        metricName: 'discount_to_nav',
        value: '9.2',
        unit: 'percent',
        status: 'warning',
        confidence: '0.9',
        metadata: JSON.stringify({ source: 'seeded_data', bdcs: ['ARCC', 'OCSL', 'MAIN'] }),
        createdAt: now,
        updatedAt: now
      },
      {
        id: 'credit_fund_gross_asset_value_seed',
        dataSource: 'credit_fund',
        metricName: 'gross_asset_value',
        value: '90000000000',
        unit: 'currency',
        status: 'healthy',
        confidence: '0.9',
        metadata: JSON.stringify({ source: 'seeded_data', quarter: 'Q4-2023' }),
        createdAt: now,
        updatedAt: now
      },
      {
        id: 'bank_provision_non_bank_financial_provisions_seed',
        dataSource: 'bank_provision',
        metricName: 'non_bank_financial_provisions',
        value: '13.4',
        unit: 'percent',
        status: 'critical',
        confidence: '0.85',
        metadata: JSON.stringify({ source: 'seeded_data', banks: ['JPM', 'BAC', 'WFC'] }),
        createdAt: now,
        updatedAt: now
      }
    ];

    for (const data of seedData) {
      try {
        await db.insert(metrics).values(data);
      } catch (error) {
        if (error.message.includes('Duplicate entry')) {
          console.log('ℹ️  Metric already exists:', data.id);
        } else {
          throw error;
        }
      }
    }
    
    console.log('✅ Initial metrics data seeded successfully');
  } catch (error) {
    console.error('❌ Error seeding metrics:', error.message);
  }
}

seedMetrics();
"

echo ""
echo "✅ Database setup complete!"
echo ""
echo "Next steps:"
echo "1. Update your .env.local file with the database credentials"
echo "2. Start the development server: npm run dev"
echo "3. Visit http://localhost:3000"
echo "4. Login with test@example.com / testpassword123"
echo ""
echo "Database connection details:"
echo "Host: ${DATABASE_HOST:-localhost}"
echo "Database: boom_bust_sentinel"
echo "User: ${DATABASE_USERNAME:-sentinel_user}"
echo "Password: ${DATABASE_PASSWORD:-sentinel_password}"
