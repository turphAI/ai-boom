#!/bin/bash

# PlanetScale Database Setup Script
# This script sets up the database schema and initial data for the Boom-Bust Sentinel dashboard

set -e

echo "🚀 Setting up PlanetScale database for Boom-Bust Sentinel..."

# Check if required environment variables are set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    echo "Please set your PlanetScale connection string:"
    echo "export DATABASE_URL='mysql://username:password@host/database?sslaccept=strict'"
    exit 1
fi

# Check if pscale CLI is installed
if ! command -v pscale &> /dev/null; then
    echo "⚠️  PlanetScale CLI not found. Installing..."
    if command -v brew &> /dev/null; then
        brew install planetscale/tap/pscale
    else
        echo "❌ Please install the PlanetScale CLI manually:"
        echo "https://github.com/planetscale/cli#installation"
        exit 1
    fi
fi

# Parse database name from DATABASE_URL
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
if [ -z "$DB_NAME" ]; then
    DB_NAME="boom_bust_sentinel"
fi

echo "📊 Database name: $DB_NAME"

# Create development branch if it doesn't exist
echo "🌿 Creating development branch..."
pscale branch create $DB_NAME development --if-not-exists || true

# Generate and push schema changes
echo "📝 Generating database migrations..."
npm run db:generate

echo "🔄 Pushing schema to development branch..."
pscale deploy-request create $DB_NAME development --notes "Initial schema setup for Boom-Bust Sentinel dashboard"

echo "✅ Database setup complete!"
echo ""
echo "Next steps:"
echo "1. Review the deploy request in PlanetScale dashboard"
echo "2. Deploy the changes to main branch"
echo "3. Update your production DATABASE_URL in Vercel"
echo ""
echo "For local development, create a connection:"
echo "pscale connect $DB_NAME development --port 3309"
echo "Then update your .env.local with the local connection string"